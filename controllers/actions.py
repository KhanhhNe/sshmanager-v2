from datetime import datetime
from typing import List

import psutil
from pony.orm import ObjectNotFound, db_session

from controllers import putty_controllers
from controllers.tasks import logger
from models.port_models import Port
from models.ssh_models import SSH


async def check_ssh_status(ssh: SSH):
    """
    Check for SSH live/die status and save to db
    :param ssh: Target SSH
    """
    is_live = await putty_controllers.verify_ssh(ssh.ip,
                                                 ssh.username,
                                                 ssh.password)

    with db_session:
        try:
            ssh: SSH = SSH.get_for_update(id=ssh.id)
        except ObjectNotFound:
            return

        ssh.last_checked = datetime.now()
        ssh.is_live = is_live
        ssh.is_checking = False


async def check_port_ip(port: Port):
    """
    Check for port's external IP and save to db
    :param port: Target port
    """
    ip = await putty_controllers.get_proxy_ip(port.proxy_address)

    with db_session:
        try:
            port: Port = Port.get_for_update(id=port.id)
        except ObjectNotFound:
            return

        if not ip and port.time_connected is not None:
            port.ssh = None
            port.time_connected = None
            logger.info(f"Port {port.port} - {port.ip} died!")

        port.ip = ip
        port.last_checked = datetime.now()
        port.is_checking = False


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port and save to db
    :param port: Target port
    :param ssh: SSH to perform port-forwarding
    """
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
            port: Port = Port.get_for_update(id=port.id)
            ssh: SSH = SSH.get_for_update(id=ssh.id)
        except ObjectNotFound:
            return

        if is_connected:
            port.time_connected = datetime.now()
            port.ip = ssh.ip
        else:
            port.ssh = None
            ssh.is_live = False


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in SSH.select().for_update():
            ssh.is_checking = False
        for port in Port.select().for_update():
            port.is_checking = False
            port.ip = ''
            port.ssh = None
            port.time_connected = None


def kill_child_processes():
    """
    Kill all child processes started by the application
    """
    process = psutil.Process()
    children: List[psutil.Process] = process.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children)
