import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import aiohttp
import trio
from pony.orm import db_session
from trio_asyncio import aio_as_trio

import config
from controllers import actions
from models import Port, SSH

logger = logging.getLogger('Tasks')


class CheckTask(ABC):
    def __init__(self):
        self.limit = trio.CapacityLimiter(self.tasks_limit)
        self.included_ids = []

    @property
    @abstractmethod
    def tasks_limit(self):
        """
        Maximum concurrent tasks.
        """

    @abstractmethod
    def get_objects(self):
        """
        Get objects to run tasks on.

        :return: Objects iterable
        """

    @abstractmethod
    async def run_on_object(self, obj):
        """
        Run task with a given object until self.is_running is False.

        :param obj: Target object
        """

    async def run_task(self):
        async def _auto_cancel(target_obj, cancel_scope: trio.CancelScope):
            while True:
                if target_obj.id not in self.included_ids:
                    cancel_scope.cancel()
                await trio.sleep(0)

        async def _run_with_auto_cancel(target_obj):
            async with trio.open_nursery() as task_nursery:
                task_nursery.start_soon(_auto_cancel, target_obj, task_nursery.cancel_scope)
                await self.run_on_object(target_obj)

        async with trio.open_nursery() as nursery:
            while True:
                not_checked = self.included_ids.copy()

                # Try to add new tasks
                with db_session:
                    for obj in self.get_objects():
                        if obj.id in not_checked:
                            not_checked.remove(obj.id)
                            continue
                        self.included_ids.append(obj.id)
                        nursery.start_soon(_run_with_auto_cancel, obj)

                # Remove not checked objects
                for obj_id in not_checked:
                    self.included_ids.remove(obj_id)

                self.limit.total_tokens = self.tasks_limit
                await trio.sleep(1)


class SSHCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return config.get('ssh_tasks_count')

    def get_objects(self):
        return SSH.select()

    async def run_on_object(self, obj):
        while True:
            async with self.limit:
                await actions.check_ssh_status(obj)
            await trio.sleep(60)


class PortCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return 100

    def get_objects(self):
        return Port.select()

    async def run_on_object(self, port: Port):
        while True:
            # Sleep first to make the bellow continues easier
            await trio.sleep(0)

            async with trio.open_nursery() as nursery:
                async with self.limit:
                    with db_session:
                        port: Port = Port[port.id].load_object()

                    if port.is_connected:
                        ip = await actions.check_port_ip(port)
                        if ip != port.ssh.ip:
                            port.disconnect_ssh()

                    # Connect SSH to port
                    if port.need_ssh:
                        ssh = SSH.get_ssh_for_port(port, unique=config.get('use_unique_ssh'))
                        if ssh is None:
                            continue

                        port.assign_ssh(ssh)
                        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTING")
                        await actions.connect_ssh_to_port(ssh, port)
                    # Reset port's SSH after a determined time
                    else:
                        if not config.get('auto_reset_ports'):
                            continue

                        reset_interval = config.get('port_reset_interval')
                        time_expired = datetime.now() - timedelta(seconds=reset_interval)
                        if not port.need_reset(time_expired):
                            continue

                        logger.info(f"Resetting port {port.port_number}")
                        nursery.start_soon(actions.reset_ports, [port])


async def download_sshstore_ssh():
    while True:
        interval = config.get('sshstore_interval')
        await asyncio.sleep(interval)

        if not config.get('sshstore_enabled'):
            continue

        api_key = config.get('sshstore_api_key')
        country = config.get('sshstore_country')
        limit = config.get('sshstore_limit')

        # noinspection PyBroadException
        try:
            async with aio_as_trio(aiohttp.ClientSession()) as client:
                resp = await aio_as_trio(client.get)(f"http://autossh.top/api/txt/{api_key}/{country}/{limit}")
                actions.insert_ssh_from_file_content(await aio_as_trio(resp.text)())
        except Exception:
            pass


async def run_all_tasks():
    async with trio.open_nursery() as nursery:
        ssh_check = SSHCheckTask()
        port_check = PortCheckTask()
        nursery.start_soon(ssh_check.run_task)
        nursery.start_soon(port_check.run_task)
        nursery.start_soon(aio_as_trio(download_sshstore_ssh))
