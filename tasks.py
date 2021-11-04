import asyncio
import logging
from datetime import datetime
from typing import List

import psutil
from pony.orm import ObjectNotFound, db_session, desc

import config
from controllers import putty_controllers
from models.port_models import Port
from models.ssh_models import SSH

logger = logging.getLogger('Tasks')


async def ssh_task():
    while True:
        conf = config.get_config()
        workers_count = conf.getint('WEB', 'workers')
        ssh_tasks_count = conf.getint('SSH', 'tasks_count')
        ssh_tasks_count //= workers_count
        tasks = []

        with db_session:
            # Check SSH for live/die status
            checking_ssh = SSH \
                .select() \
                .filter(lambda obj: obj.is_checking is False) \
                .order_by(lambda obj: obj.last_checked) \
                .limit(ssh_tasks_count)
            for ssh in checking_ssh:
                tasks.append(check_ssh_status(ssh))

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.5)


async def port_task():
    while True:
        conf = config.get_config()
        workers_count = conf.getint('WEB', 'workers')
        port_tasks_count = conf.getint('PORT', 'tasks_count')
        port_tasks_count //= workers_count
        tasks = []

        with db_session:
            # Check port for external IP
            checking_ports = Port \
                .select() \
                .filter(lambda obj: not obj.is_checking) \
                .filter(lambda obj: obj.ssh is not None) \
                .order_by(lambda obj: obj.last_checked) \
                .limit(port_tasks_count)
            for port in checking_ports:
                tasks.append(check_port_ip(port))

            # Connect ports to empty SSH
            connecting_ports = Port \
                .select(lambda p: not p.ssh) \
                .limit(port_tasks_count)
            # Get latest SSHs
            connecting_ssh = SSH \
                .select(lambda s: s.is_live and not s.port) \
                .order_by(desc(SSH.last_checked)) \
                .limit(len(connecting_ports))

            for port, ssh in zip(connecting_ports, connecting_ssh):
                tasks.append(connect_ssh_to_port(ssh, port))

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.5)


async def check_ssh_status(ssh: SSH):
    """
    Check for SSH live/die status and save to db
    :param ssh: Target SSH
    """
    with db_session:
        SSH[ssh.id].is_checking = True

    is_live = await putty_controllers.verify_ssh(ssh.ip,
                                                 ssh.username,
                                                 ssh.password)

    with db_session:
        try:
            ssh: SSH = SSH[ssh.id]
            ssh.last_checked = datetime.now()
            ssh.is_live = is_live
            ssh.is_checking = False
        except ObjectNotFound:
            pass


async def check_port_ip(port: Port):
    """
    Check for port's external IP and save to db
    :param port: Target port
    """
    with db_session:
        Port[port.id].is_checking = True

    ip = await putty_controllers.get_proxy_ip(port.proxy_address)

    with db_session:
        try:
            port: Port = Port[port.id]
            port.last_checked = datetime.now()
            port.ip = ip

            # Remove SSH assignment if the port is not usable anymore after
            # connecting to the SSH so that other SSH could be assigned to
            # this port
            if not port.ip and port.is_connected_to_ssh:
                port.ssh = None
                port.is_connected_to_ssh = False
            port.is_checking = False
        except ObjectNotFound:
            pass


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port and save to db
    :param port: Target port
    :param ssh: SSH to perform port-forwarding
    """
    with db_session:
        Port[port.id].ssh = SSH[ssh.id]

    try:
        await putty_controllers.connect_ssh(ssh.ip, ssh.username, ssh.password,
                                            port=port.port)
        is_connected = True
        logger.info(f"Port {port.port} connected to SSH {ssh.ip}")
    except putty_controllers.PuttyError:
        is_connected = False
        logger.info(f"Port {port.port} failed to connect to SSH {ssh.ip}")

    with db_session:
        try:
            port: Port = Port[port.id]
            ssh: SSH = SSH[ssh.id]

            # Mark port as connected if connection succeed. Otherwise remove
            # the SSH assignment
            if is_connected:
                port.is_connected_to_ssh = True
                port.ip = ssh.ip
            else:
                port.ssh = None
                ssh.is_live = False
        except ObjectNotFound:
            pass


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
