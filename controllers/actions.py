import logging
from typing import List

import trio
from pony.orm import commit, db_session
from trio_asyncio import aio_as_trio

import utils
from controllers import ssh_controllers
from models import Port, SSH

logger = logging.getLogger('Actions')


async def check_port_ip(port: Port):
    """
    Check for port's external IP.

    :param port: Target port
    :return:
    """
    Port.begin_checking(port)
    ip = await aio_as_trio(utils.get_proxy_ip)(port.proxy_address)
    Port.end_checking(port, public_ip=ip)
    return ip


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port.

    :param port: Target port
    :param ssh: Connecting SSH
    """
    try:
        await aio_as_trio(ssh_controllers.connect_ssh)(
            ssh.ip, ssh.username, ssh.password, port=port.port_number
        )
        is_connected = True
        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTED SUCCESSFULLY")
    except ssh_controllers.SSHError:
        is_connected = False
        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTION FAILED")

    with db_session:
        port = Port[port.id]
        port.is_connected = is_connected
        if not is_connected:
            port.disconnect_ssh(remove_from_used=True)


async def reconnect_port_using_ssh(port: Port, ssh: SSH):
    """
    Kill all SSHs running on given Port and connect given SSH into the Port.

    :param port: Port
    :param ssh: SSH
    """
    logger.debug(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - RECONNECTING")
    await connect_ssh_to_port(ssh, port)
    logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - RECONNECTED SUCCESSFULLY")


async def reset_ports(ports: List[Port], unique=True, delete_ssh=False):
    """
    Reset ports and reconnect to new SSH.

    :param ports: Ports to reset
    :param unique: Set to True if all SSH used for a Port cannot be used again
    for the same Port
    :param delete_ssh: Set to True to delete all used SSHs
    """
    async with trio.open_nursery() as nursery:
        with db_session:
            for port in ports:
                # Disconnect SSH from port
                port = Port[port.id]  # Load port.ssh
                used_ssh = port.ssh
                port.disconnect_ssh(used_ssh)
                if delete_ssh:
                    used_ssh.delete()

                # Reconnect new SSH to port
                ssh = SSH.get_ssh_for_port(port, unique=unique)
                if ssh:
                    port.assign_ssh(ssh)
                    nursery.start_soon(reconnect_port_using_ssh, port, ssh)


def reset_entities_data():
    """
    Reset SSH and Port data from previous application run.
    """
    with db_session:
        for ssh in SSH.select():
            ssh.reset_status()
        for port in Port.select():
            port.reset_status()
    logger.debug("Status reset is done")


def insert_ssh_from_file_content(file_content):
    """
    Insert SSH into database from file content. Will skip SSH that are already
    in the database.

    :param file_content: SSH file content
    :return: List of created SSH
    """
    created_ssh = []
    with db_session:
        for ssh_info in utils.parse_ssh_file(file_content):
            if not SSH.exists(**ssh_info):
                created_ssh.append(SSH(**ssh_info))
        commit()
    logger.info(f"Inserted {len(created_ssh)} SSH from file content")

    return [ssh.id for ssh in created_ssh]
