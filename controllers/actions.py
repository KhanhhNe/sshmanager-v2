import asyncio
import logging
from typing import List

import psutil
from pony.orm import db_session

import utils
from controllers import putty_controllers
from models import Port, SSH

logger = logging.getLogger('Actions')


async def check_ssh_status(ssh: SSH):
    """
    Check for SSH live/die status and save to db

    :param ssh: Target SSH
    """
    is_live = await putty_controllers.verify_ssh(ssh.ip,
                                                 ssh.username,
                                                 ssh.password)

    with db_session:
        SSH.end_checking(ssh, is_live=is_live)


async def check_port_ip(port: Port):
    """
    Check for port's external IP and save to db

    :param port: Target port
    """
    ip = await putty_controllers.get_proxy_ip(port.proxy_address)

    with db_session:
        Port.end_checking(port,
                          external_ip=ip)


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port.

    :param port: Target port
    :param ssh: Connecting SSH
    """
    try:
        await putty_controllers.connect_ssh(ssh.ip, ssh.username, ssh.password,
                                            port=port.port_number)
        is_connected = True
        logger.info(f"Port {port.port_number} "
                    f"connected to SSH {ssh.ip}")
    except putty_controllers.PuttyError:
        is_connected = False
        logger.info(f"Port {port.port_number} "
                    f"failed to connect to SSH {ssh.ip}")

    with db_session:
        if not is_connected:
            port.disconnect_ssh(ssh, remove_from_used=True)


async def reconnect_port_using_ssh(port: Port, ssh: SSH):
    """
    Kill all SSHs running on given Port and connect given SSH into the Port.

    :param port: Port
    :param ssh: SSH
    """
    logger.debug(f"Killing processes on port {port.port_number}")
    await utils.kill_process_on_port(port.port_number)
    logger.debug(f"Reconnecting port {port.port_number}")
    await connect_ssh_to_port(ssh, port)
    logger.info(f"Port {port.port_number} has been reset")


async def reset_ports(ports: List[Port], unique=True, delete_ssh=False):
    """
    Reset ports and reconnect to new SSH.

    :param ports: Ports to reset
    :param unique: Set to True if all SSH used for a Port cannot be used again
    for the same Port
    :param delete_ssh: Set to True to delete all used SSHs
    """
    with db_session:
        for port in ports:
            port = Port[port.id]
            used_ssh = port.ssh
            port.disconnect_ssh(used_ssh)
            if delete_ssh:
                used_ssh.delete()

            ssh = SSH.get_ssh_for_port(port, unique=unique)
            port.connect_to_ssh(ssh)
            asyncio.ensure_future(reconnect_port_using_ssh(port, ssh))


def reset_old_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in SSH.select():
            ssh.reset_status()
        for port in Port.select():
            port.reset_status()


def kill_child_processes():
    """
    Kill all child processes started by the application
    """
    process = psutil.Process()
    children: List[psutil.Process] = process.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children)
