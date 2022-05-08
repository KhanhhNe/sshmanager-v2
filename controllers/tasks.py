import asyncio
import logging
import time
from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Dict

import aiohttp
import trio
import trio_asyncio
from pony.orm import db_session

import config
from controllers import actions
from models import Port, SSH

logger = logging.getLogger('Tasks')


class DynamicSemaphore(asyncio.Semaphore):
    def adjust_limit(self, value):
        self._value = value


class CheckTask(ABC):
    def __init__(self):
        self.semaphore = DynamicSemaphore(self.tasks_limit)
        self.is_running = True
        self.tasks: Dict[int, asyncio.Task] = {}

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
    async def task_run(self, obj):
        """
        Run task with a given object until self.is_running is False.

        :param obj: Target object
        """

    async def sleep(self, sleep_duration):
        start = time.time()
        while self.is_running:
            await asyncio.sleep(1)
            if time.time() - start >= sleep_duration:
                break

    async def run(self):
        while self.is_running:
            not_checked = list(self.tasks.keys())

            # Try to add new tasks
            with db_session:
                for obj in self.get_objects():
                    if obj.id in not_checked:
                        not_checked.remove(obj.id)
                        continue
                    self.tasks[obj.id] = asyncio.create_task(self.task_run(obj))

            # Cancel and remove tasks associated with deleted objects
            for obj_id in not_checked:
                task = self.tasks[obj_id]
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
                del self.tasks[obj_id]

            self.semaphore.adjust_limit(self.tasks_limit)
            await self.sleep(10)

    async def stop(self):
        self.is_running = False


class SSHCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return config.get('ssh_tasks_count')

    def get_objects(self):
        return SSH.select()

    async def task_run(self, obj):
        while self.is_running:
            async with self.semaphore:
                await actions.check_ssh_status(obj)
            await self.sleep(60)


class PortCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return 100

    def get_objects(self):
        return Port.select()

    async def task_run(self, port: Port):
        while self.is_running:
            async with self.semaphore:
                await actions.check_port_ip(port)

                with db_session:
                    need_ssh = port.need_ssh
                if need_ssh:
                    with db_session:
                        ssh = SSH.get_ssh_for_port(port, unique=config.get('use_unique_ssh'))

                    if ssh is not None:
                        with db_session:
                            port.assign_ssh(ssh)
                        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTING")
                        await actions.connect_ssh_to_port(ssh, port)
                else:
                    if config.get('auto_reset_ports'):
                        reset_interval = config.get('port_reset_interval')
                        time_expired = datetime.now() - timedelta(seconds=reset_interval)
                        with db_session:
                            need_reset = port.need_reset(time_expired)
                        if need_reset:
                            logger.info(f"Resetting port {port.port_number}")
                            await actions.reset_ports([port])

            await self.sleep(1)


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
            async with aiohttp.ClientSession() as client:
                resp = await client.get(
                    f"http://autossh.top/api/txt/{api_key}/{country}/{limit}"
                )
                await actions.insert_ssh_from_file_content(await resp.text())
        except Exception:
            pass


async def run_all_tasks():
    async with trio.open_nursery() as nursery:
        ssh_check = SSHCheckTask()
        nursery.start_soon(trio_asyncio.aio_as_trio(ssh_check.run))
        port_check = PortCheckTask()
        nursery.start_soon(trio_asyncio.aio_as_trio(port_check.run))
        nursery.start_soon(trio_asyncio.aio_as_trio(download_sshstore_ssh))
