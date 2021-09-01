import asyncio
from datetime import datetime
from functools import wraps
from typing import List, Type, Union, cast

import psutil
from pony.orm import db_session

from controllers import bitvise_controllers
from models.port_models import Port
from models.ssh_models import SSH


def runners(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        await asyncio.gather(*[func(*args, **kwargs) for _ in range(20)])

    return cast(func, wrapped)


@db_session
def get_check_next(cls: Union[Type[SSH], Type[Port]]):
    """
    Get next SSH/Port to check
    :param cls: SSH or Port (the Entity)
    :return: Next SSH/Port to check if there is one. None otherwise
    """
    next_obj = cls \
        .select() \
        .filter(lambda obj: obj.is_checking is False) \
        .order_by(lambda obj: obj.last_checked) \
        .first()
    if next_obj:
        next_obj.is_checking = True
        return next_obj
    else:
        return None


@runners
async def ssh_check_task():
    """
    Check and update SSH status one by one
    """
    while True:
        # Reduce system load
        await asyncio.sleep(5)

        next_ssh = get_check_next(SSH)
        if not next_ssh:
            continue

        is_live = await bitvise_controllers.verify_ssh(next_ssh.ip,
                                                       next_ssh.username,
                                                       next_ssh.password)
        with db_session:
            ssh: SSH = SSH[next_ssh.id]
            if ssh:
                ssh.last_checked = datetime.now()
                ssh.is_live = is_live
            ssh.is_checking = False


@runners
async def port_check_task():
    """
    Check and update port status (can proxy through or not) one by one
    """
    while True:
        # Reduce system load
        await asyncio.sleep(5)

        next_port = get_check_next(Port)
        if not next_port:
            continue

        ip = await bitvise_controllers.get_proxy_ip(next_port.proxy_address)
        with db_session:
            port: Port = Port[next_port.id]
            if port:
                port.last_checked = datetime.now()
                port.ip = ip

                # Remove SSH assignment if the port is not usable anymore after
                # connecting to the SSH so that other SSH could be assigned to
                # this port
                if not port.ip and port.is_connected_to_ssh:
                    port.ssh = None
                    port.is_connected_to_ssh = False
                port.is_checking = False


@runners
async def port_connect_task():
    """
    Assign and connect live SSH to unconnected ports
    """
    while True:
        await asyncio.sleep(5)

        with db_session:
            # Get unassigned ports
            port: Port = Port.select(lambda p: not p.ssh).first()
            if not port:
                continue

            # Get free live SSH (not assigned to any port)
            ssh: SSH = SSH.select(lambda s: s.is_live and not s.port).first()
            if not ssh:
                continue

            # Assign SSH to port so other tasks won't try to assign another SSH
            # to this port again
            port.ssh = ssh

        try:
            await bitvise_controllers.connect_ssh(ssh.ip,
                                                  ssh.username,
                                                  ssh.password,
                                                  port=port.port)
            is_connected = True
        except bitvise_controllers.BitviseError:
            is_connected = False

        with db_session:
            port = Port[port.id]
            if not port:
                continue

            # Mark port as connected if connection succeed. Otherwise remove
            # the SSH assignment
            if is_connected:
                port.is_connected_to_ssh = True
            else:
                port.ssh = None


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in SSH.select():
            ssh.is_checking = False
        for port in Port.select():
            port.is_checking = False
            port.ip = ''
            port.ssh = None
            port.is_connected_to_ssh = False


def kill_child_processes():
    """
    Kill all child processes started by the application
    """
    process = psutil.Process()
    children: List[psutil.Process] = process.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children)
