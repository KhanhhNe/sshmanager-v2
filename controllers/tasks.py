import asyncio

from controllers import bitvise_controllers

from models import ssh_models


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
