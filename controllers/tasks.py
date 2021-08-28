import asyncio

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
            is_live = await bitvise_controllers.verify_ssh(next_ssh.ip, next_ssh.username, next_ssh.password)
            next_ssh.is_live = is_live


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
            is_live = bool(await bitvise_controllers.get_proxy_ip(next_port.proxy_address))
            next_port.is_live = is_live


async def port_check_task():
    """
    Wrapper for concurrent run of _port_check_runner()
    """
    await asyncio.gather(*[_port_check_runner() for _ in range(20)])
