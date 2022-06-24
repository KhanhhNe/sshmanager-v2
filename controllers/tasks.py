import logging
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import aiohttp
import trio
from pony.orm import db_session
from pony.orm.core import Query
from trio_asyncio import aio_as_trio

import config
import utils
from controllers import actions, ssh_controllers
from models import Port, SSH

logger = logging.getLogger('Tasks')


class IDManager:
    def __init__(self):
        self.ids = {}

    def add(self, obj_id):
        self.ids[obj_id] = True

    def remove(self, obj_id):
        if obj_id in self.ids:
            del self.ids[obj_id]

    def include(self, obj_id):
        return bool(self.ids.get(obj_id))

    def get_ids(self):
        return list(self.ids.keys())


class CheckTask(ABC):
    def __init__(self):
        self.limit = trio.CapacityLimiter(self.tasks_limit)
        self.included_ids = IDManager()

    @property
    @abstractmethod
    def tasks_limit(self):
        """
        Maximum concurrent tasks.
        """

    @abstractmethod
    def get_objects(self) -> Query:
        """
        Get objects to run tasks on.

        :return: Objects iterable
        """

    def _get_objects_list(self):
        with db_session(optimistic=False):
            return self.get_objects()[:].to_list()

    @abstractmethod
    async def run_on_object(self, obj):
        """
        Run task with a given object until self.is_running is False.

        :param obj: Target object
        """

    async def run_task(self):
        async def _auto_cancel(target_obj, cancel_scope: trio.CancelScope):
            while True:
                if not self.included_ids.include(target_obj.id):
                    cancel_scope.cancel()
                await trio.sleep(0)

        async def _run_with_auto_cancel(target_obj):
            async with trio.open_nursery() as task_nursery:
                task_nursery.start_soon(_auto_cancel, target_obj, task_nursery.cancel_scope)
                await self.run_on_object(target_obj)

        async with trio.open_nursery() as nursery:
            while True:
                not_checked = self.included_ids.get_ids()
                added = []

                # Try to add new tasks
                objects = await trio.to_thread.run_sync(self._get_objects_list)

                for obj in objects:
                    if obj.id in not_checked:
                        not_checked.remove(obj.id)
                        continue
                    added.append(obj)

                for obj in added:
                    self.included_ids.add(obj.id)
                    nursery.start_soon(_run_with_auto_cancel, obj)
                    await trio.sleep(0)

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
            SSH.begin_checking(obj)
            start_time = time.perf_counter()
            ssh_info = f"{obj.ip:15} |      "
            connection_succeed = await utils.test_ssh_connection(obj.ip)
            run_time = '{:4.1f}'.format(time.perf_counter() - start_time)

            if connection_succeed:
                async with self.limit:
                    is_live = await aio_as_trio(ssh_controllers.verify_ssh)(obj.ip, obj.username, obj.password)
                    SSH.end_checking(obj, is_live=is_live)
            else:
                logging.getLogger('Ssh').debug(f"{ssh_info} ({run_time}s) - Cannot connect to SSH port.")
                SSH.end_checking(obj, is_live=False)

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
                        port = Port.select(lambda p: p.id == port.id).prefetch(SSH).first().load_object()

                    if port.is_connected:
                        ip = await actions.check_port_ip(port)
                        if port.ssh and ip != port.ssh.ip:
                            logger.info(f"Port {port.port_number:<5} -> SSH {port.ssh.ip:<15} - PROXY DIED")
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

                        logger.info(f"Port {port.port_number:<5} -> RESETTING")
                        nursery.start_soon(actions.reset_ports, [port])


async def download_sshstore_ssh():
    while True:
        if not config.get('sshstore_enabled'):
            await trio.sleep(0)
            continue

        api_key = config.get('sshstore_api_key')
        country = config.get('sshstore_country')

        # noinspection PyBroadException
        try:
            async with aio_as_trio(aiohttp.ClientSession()) as client:
                resp = await aio_as_trio(client.get)(f"http://autossh.top/api/txt/{api_key}/{country}/")
                await trio.to_thread.run_sync(actions.insert_ssh_from_file_content, await aio_as_trio(resp.text)())
        except Exception:
            logger.debug(traceback.format_exc())
            pass

        await trio.sleep(60)


async def run_all_tasks():
    async with trio.open_nursery() as nursery:
        await trio.sleep(1)
        ssh_check = SSHCheckTask()
        port_check = PortCheckTask()
        nursery.start_soon(ssh_check.run_task)
        nursery.start_soon(port_check.run_task)
        nursery.start_soon(download_sshstore_ssh)
        logger.debug("Tasks started")
