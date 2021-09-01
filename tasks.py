import asyncio
from functools import wraps
from typing import List, Type, Union, cast

import psutil
from pony.orm import db_session

from controllers import bitvise_controllers
from models import port_models, ssh_models


def runners(func):
    @wraps
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

        next_ssh = get_check_next(ssh_models.SSH)
        if not next_ssh:
            continue

        is_live = await bitvise_controllers.verify_ssh(next_ssh.ip,
                                                       next_ssh.username,
                                                       next_ssh.password)
        with db_session:
            ssh: SSH = ssh_models.SSH[next_ssh.id]
            if ssh:
                ssh.last_checked = datetime.now()
                ssh.is_live = is_live


@runners
async def port_check_task():
    """
    Check and update port status (can proxy through or not) one by one
    """
    while True:
        # Reduce system load
        await asyncio.sleep(5)

        next_port = get_check_next(port_models.Port)
        if not next_port:
            continue

        ip = await bitvise_controllers.get_proxy_ip(next_port.proxy_address)
        with db_session:
            port: Port = port_models.Port[next_port.id]
            if port:
                port.last_checked = datetime.now()
                port.ip = ip


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in ssh_models.SSH.select():
            ssh.is_checking = False
        for port in port_models.Port.select():
            port.is_checking = False


def kill_child_processes():
    """
    Kill all child processes started by the application
    """
    process = psutil.Process()
    children: List[psutil.Process] = process.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children)
