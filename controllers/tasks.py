import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import aiohttp
import trio
from pony import orm
from pony.orm import db_session
from pony.orm.core import Query
from trio_asyncio import aio_as_trio

import config
import models.common
import utils
from controllers import actions, ssh_controllers
from models import Port, SSH

logger = logging.getLogger('Tasks')


class CheckTask(ABC):
    def __init__(self):
        self.limit = trio.CapacityLimiter(self.tasks_limit)

    @property
    @abstractmethod
    def tasks_limit(self):
        """
        Maximum concurrent tasks.
        """

    @property
    @abstractmethod
    def sleep_interval(self):
        """
        Sleep interval between tasks.
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
        Run task on an object.

        :param obj: Object to run task on.
        """

    async def run_task(self):
        async def _run(target_obj):
            while True:
                try:
                    with db_session:
                        target_obj = models.common.renew_object(target_obj).load()
                    await self.run_on_object(target_obj)
                except orm.ObjectNotFound:
                    break
                await trio.sleep(self.sleep_interval)

        async with trio.open_nursery() as nursery:
            id_included = {}

            while True:
                objects = await trio.to_thread.run_sync(self._get_objects_list)

                # Convert to set for efficient operations later
                tasks_ids = set(id_included.keys())
                object_ids = set(o.id for o in objects)
                objects_by_id = {obj.id: obj for obj in objects}

                # Try to add new tasks
                if added := object_ids - tasks_ids:
                    for index, obj_id in enumerate(added):
                        id_included[obj_id] = True
                        nursery.start_soon(_run, objects_by_id[obj_id])
                        await trio.sleep(0)

                # Remove tasks not in the database anymore
                elif removed := tasks_ids - object_ids:
                    for index, obj_id in enumerate(removed):
                        del id_included[obj_id]
                        await trio.sleep(0)

                self.limit.total_tokens = self.tasks_limit
                await trio.sleep(5)


class SSHCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return config.get('ssh_tasks_count')

    @property
    def sleep_interval(self):
        return 60

    @property
    def test_timeout(self):
        return config.get('ssh_test_timeout')

    def get_objects(self):
        return SSH.select()

    async def run_on_object(self, ssh: SSH):
        ssh_info = f"{ssh.ip:15} |      "

        def run_time(start):
            return '{:4.1f}'.format(trio.current_time() - start)

        async with self.limit:
            start_time = trio.current_time()

            try:
                with trio.fail_after(self.test_timeout):
                    is_live = await aio_as_trio(ssh_controllers.verify_ssh)(ssh.ip, ssh.username, ssh.password)
            except trio.TooSlowError:
                # Timeout exceeded
                logging.getLogger('Ssh').debug(f"{ssh_info} ({run_time(start_time)}s) - Test timeout exceeded.")
                is_live = False

            await ssh.update_check_result(is_live=is_live)

            # Auto delete the died SSH if requested
            if not is_live and config.get('ssh_auto_delete_died'):
                await trio.to_thread.run_sync(ssh.delete_if_died)


class PortCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return 100

    @property
    def sleep_interval(self):
        return 0

    def get_objects(self):
        return Port.select()

    async def run_on_object(self, port: Port):
        async with trio.open_nursery() as nursery:
            async with self.limit:
                with db_session:
                    if port := Port.select(lambda p: p.id == port.id).prefetch(SSH).first():
                        port.load()
                    else:
                        return

                # Update port ip
                if port.is_connected:
                    ip = await aio_as_trio(utils.get_proxy_ip)(port.proxy_address, tries=3)
                    await port.update_check_result(public_ip=ip)

                # Remove SSH if port is not connected anymore
                if config.get('port_auto_replace_died_ssh'):
                    if port.is_connected and port.last_checked and not port.public_ip:
                        logger.info(f"Port {port.port_number:<5} -> SSH {port.ssh.ip:<15} - PROXY DIED")
                        port.disconnect_ssh()

                # Connect SSH to port
                if port.need_ssh:
                    ssh = SSH.get_ssh_for_port(port, unique=config.get('use_unique_ssh'))
                    if ssh is None:
                        return

                    port.assign_ssh(ssh)
                    logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTING")
                    await actions.connect_ssh_to_port(ssh, port)

                # Reset port's SSH after a determined time
                if config.get('auto_reset_ports'):
                    reset_interval = config.get('port_reset_interval')
                    time_expired = datetime.now() - timedelta(seconds=reset_interval)
                    if not port.need_reset(time_expired):
                        return

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
