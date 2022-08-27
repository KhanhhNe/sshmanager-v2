import asyncio
import logging
from typing import List

from pony.orm import commit, db_session

import utils
from controllers import ssh_controllers
from models import Port, SSH

logger = logging.getLogger('Actions')


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port.

    :param port: Target port
    :param ssh: Connecting SSH
    """
    try:
        await asyncio.wait_for(ssh_controllers.connect_ssh(ssh.ip, ssh.username, ssh.password, port=port.port_number),
                               timeout=60)
        is_connected = True
        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTED SUCCESSFULLY")
    except (ssh_controllers.SSHError, asyncio.TimeoutError) as exc:
        is_connected = False
        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTION FAILED - {exc.args}")

    with db_session():
        Port[port.id].is_connected = is_connected
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
    :param unique: Set to True if all SSH used for _run_with_reset_is_working Port cannot be used again
    for the same Port
    :param delete_ssh: Set to True to delete all used SSHs
    """
    tasks = []

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
                tasks.append(asyncio.create_task(reconnect_port_using_ssh(port, ssh)))

    await asyncio.gather(*tasks)


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
    logger.debug("Inserting SSH from file content")
    created_ssh = []
    with db_session:
        for ssh_info in utils.parse_ssh_file(file_content):
            if not SSH.exists(**ssh_info):
                created_ssh.append(SSH(**ssh_info))
        commit()
    logger.info(f"Inserted {len(created_ssh)} SSH from {len(file_content.splitlines())} lines")

    return [ssh.id for ssh in created_ssh]
