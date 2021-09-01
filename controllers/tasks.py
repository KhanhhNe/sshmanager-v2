import asyncio

from pony.orm import db_session

from controllers import bitvise_controllers
from models import ports, ssh_models


async def ssh_check_task(is_runner=False):
    """
    Check and update SSH status one by one
    :param is_runner: True if this function call is to spawn child runners.
    False means this is main call.
    """
    if not is_runner:
        await asyncio.gather(
            *[ssh_check_task(is_runner=True) for _ in range(20)]
        )
    else:
        while True:
            # Reduce system load
            await asyncio.sleep(5)

            next_ssh = ssh_models.get_ssh_to_check()
            if not next_ssh:
                continue

            is_live = await bitvise_controllers.verify_ssh(next_ssh.ip,
                                                           next_ssh.username,
                                                           next_ssh.password)
            ssh_models.update_ssh_status(next_ssh, is_live=is_live)


async def port_check_task(is_runner=False):
    """
    Check and update port status (can proxy through or not) one by one
    :param is_runner: True if this function call is to spawn child runners.
    False means this is main call.
    """
    if not is_runner:
        await asyncio.gather(
            *[port_check_task(is_runner=True) for _ in range(20)]
        )
    else:
        while True:
            # Reduce system load
            await asyncio.sleep(5)

            next_port = ports.get_port_to_check()
            if not next_port:
                continue

            ip = await bitvise_controllers.get_proxy_ip(next_port.proxy_address)
            ports.update_port_ip(next_port, ip=ip)


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in ssh_models.SSH.select():
            ssh.is_checking = False
        for port in ports.Port.select():
            port.is_checking = False
