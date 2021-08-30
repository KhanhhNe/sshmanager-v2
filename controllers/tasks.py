import asyncio

from pony.orm import db_session

from controllers import bitvise_controllers
from models import ports, ssh_models


async def _ssh_check_runner():
    """
    Check and update SSH status one by one
    """
    while True:
        # Reduce system load
        await asyncio.sleep(5)

        next_ssh = ssh_models.get_ssh_to_check()
        if not next_ssh:
            continue
        with next_ssh:
            is_live = await bitvise_controllers.verify_ssh(next_ssh.ip,
                                                           next_ssh.username,
                                                           next_ssh.password)
            next_ssh.is_live = is_live
            # Delete this SSH if it is deleted from database while checking.
            # This will prevent the SSH being added again after being deleted by
            # the user.
            if not ssh_models.SSH.get(ip=next_ssh.ip,
                                      username=next_ssh.username,
                                      password=next_ssh.password):
                next_ssh.delete()


async def ssh_check_task():
    """
    Wrapper for concurrent run of _ssh_check_runner()
    """
    await asyncio.gather(*[_ssh_check_runner() for _ in range(20)])


async def _port_check_runner():
    """
    Check and update port status (can proxy through or not) one by one
    """
    while True:
        # Reduce system load
        await asyncio.sleep(5)

        next_port = ports.get_port_to_check()
        if not next_port:
            continue
        with next_port:
            ip = await bitvise_controllers.get_proxy_ip(next_port.proxy_address)
            is_usable = ip != ''
            next_port.is_usable = is_usable
            if not is_usable:
                # Remove association with linked SSH so the SSH is also be
                # marked as not used (connected by any port)
                next_port.ssh = None

            # Delete this port if it is deleted from database while checking.
            # This will prevent the port being added again after being deleted
            # by the user.
            if not ports.Port.get(port=next_port.port):
                next_port.delete()


async def port_check_task():
    """
    Wrapper for concurrent run of _port_check_runner()
    """
    await asyncio.gather(*[_port_check_runner() for _ in range(20)])


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in ssh_models.SSH.select():
            ssh.is_checking = False
        for port in ports.Port.select():
            port.is_checking = False
