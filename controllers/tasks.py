import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import aiohttp
import async_timeout
from pony.orm import db_session
from pony.orm.core import Query

import config
import utils
from controllers import actions, ssh_controllers
from models import Port, SSH

logger = logging.getLogger('Tasks')


class CheckTask(ABC):
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
        last_checked = datetime.now() - timedelta(seconds=self.sleep_interval)

        with db_session(optimistic=False):
            return (self.get_objects()
                    .filter(lambda obj: not obj.last_checked or obj.last_checked < last_checked)
                    .order_by(lambda obj: obj.last_checked)
                    .limit(self.tasks_limit)[:])

    @abstractmethod
    async def run_on_object(self, obj):
        """
        Run task on an object.

        :param obj: Object to run task on.
        """

    async def run_task(self):
        while True:
            objects = self._get_objects_list()

            if not objects:
                await asyncio.sleep(1)
                continue

            tasks = [asyncio.create_task(self.run_on_object(obj)) for obj in objects]
            await asyncio.gather(*tasks)


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
            return '{:4.1f}'.format(time.time() - start)

        start_time = time.time()

        try:
            with async_timeout.timeout(self.test_timeout):
                is_live = await ssh_controllers.verify_ssh(ssh.ip, ssh.username, ssh.password, ssh_port=ssh.ssh_port)
        except asyncio.TimeoutError:
            # Timeout exceeded
            logging.getLogger('Ssh').debug(f"{ssh_info} ({run_time(start_time)}s) - Test timeout exceeded.")
            is_live = False

        await ssh.update_check_result(is_live=is_live)

        # Auto delete the died SSH if requested
        if not is_live and config.get('ssh_auto_delete_died'):
            await asyncio.to_thread(ssh.delete_if_died)


class PortCheckTask(CheckTask):
    @property
    def tasks_limit(self):
        return 100

    @property
    def sleep_interval(self):
        return 1

    def get_objects(self):
        return Port.select(lambda port: not port.is_working)

    async def run_on_object(self, port: Port):
        with db_session:
            Port[port.id].is_working = True
        asyncio.create_task(self._run_with_reset_is_working(port))
        await asyncio.sleep(0)

    async def _run_with_reset_is_working(self, port: Port):
        try:
            await self._run_on_object(port)
        finally:
            with db_session:
                Port[port.id].is_working = False

    # noinspection PyMethodMayBeStatic
    async def _run_on_object(self, port: Port):
        with db_session:
            if port := Port.select(lambda p: p.id == port.id).prefetch(SSH).first():
                port.load()
            else:
                return

        # Update port ip
        if port.is_connected:
            ip = await utils.get_proxy_ip(port.proxy_address, tries=3)
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

        # Reset port's SSH after _run_with_reset_is_working determined time
        if config.get('auto_reset_ports'):
            reset_interval = config.get('port_reset_interval')
            time_expired = datetime.now() - timedelta(seconds=reset_interval)
            if not port.need_reset(time_expired):
                return

            logger.info(f"Port {port.port_number:<5} -> RESETTING")
            await actions.reset_ports([port])


async def download_sshstore_ssh():
    while True:
        if not config.get('sshstore_enabled'):
            await asyncio.sleep(0)
            continue

        api_key = config.get('sshstore_api_key')
        country = config.get('sshstore_country')

        # noinspection PyBroadException
        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(f"http://autossh.top/api/txt/{api_key}/{country}/")
                await asyncio.to_thread(actions.insert_ssh_from_file_content, await resp.text())
        except Exception:
            logger.debug(traceback.format_exc())
            pass

        await asyncio.sleep(60)


async def run_all_tasks():
    await asyncio.sleep(1)

    logger.debug("Tasks started")
    await asyncio.gather(
        SSHCheckTask().run_task(),
        PortCheckTask().run_task(),
        download_sshstore_ssh(),
    )
