import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from collections import deque
from contextlib import suppress
from datetime import datetime, timedelta
from inspect import isabstract, isawaitable, isclass
from typing import Deque, Dict, List, Optional, Union

import aiohttp
from pony.orm import db_session

import config
from controllers import actions
from models import Port, SSH

logger = logging.getLogger('Tasks')


class ConcurrentTask(ABC):
    """
    Run and manage a concurrent task (task that has multiple threads running
    simultaneously).
    """

    def __init__(self):
        self.tasks: List[asyncio.Task] = []
        self.is_running = False
        self._lock = asyncio.Lock()

    @property
    def task_name(self):
        return type(self).__name__

    @property
    @abstractmethod
    def tasks_limit(self):
        """
        Get maximum tasks allowed for the Task.

        :return: Maximum tasks allowed
        """
        raise NotImplementedError

    @abstractmethod
    def get_new_task(self) -> asyncio.Task:
        """
        Get a task to add to the Task.

        :return: New task
        """
        raise NotImplementedError

    async def log(self):
        sleep_duration = 10 * 60  # Seconds
        sleep_interval = 0.5  # Seconds

        while self.is_running:
            logger.debug(f"{self.task_name} is running "
                         f"(currently has {len(self.tasks)} tasks)")

            # Use small sleeping intervals to stop sooner when the Task is
            # stopped (e.g. self.running = False)
            for _ in range(int(sleep_duration / sleep_interval)):
                if self.is_running:
                    await asyncio.sleep(sleep_interval)

    async def run(self):
        """
        Run the task's loop (getting new tasks and execute them).
        """
        self.is_running = True
        asyncio.create_task(self.log())

        try:
            while self.is_running:
                new_task = self.get_new_task()
                if new_task:
                    self.tasks.append(new_task)

                await self.remove_done_tasks()
                while len(self.tasks) >= self.tasks_limit:
                    await self.remove_done_tasks()
                    await asyncio.sleep(0)

                await asyncio.sleep(0)
        except Exception:
            logger.error(traceback.format_exc())
            raise

        # Cancel running tasks
        for task in self.tasks:
            with suppress(asyncio.CancelledError):
                task.cancel()
                await task
        logger.info(f"Task killed: {type(self).__name__}")

    async def remove_done_tasks(self):
        for task in self.tasks[:]:
            if task.done():
                await task
                self.tasks.remove(task)

    async def stop(self):
        self.is_running = False


class SyncTask(ABC):
    """
    Run single threaded task. Tasks that subclass this are meant to be used in
    a same loop with all other SyncTasks.
    """

    @abstractmethod
    def run(self) -> asyncio.Task:
        """
        Run task sequentially (in same "thread" with other tasks).
        """
        pass


class SSHCheckTask(ConcurrentTask):
    """
    Task to check all SSH status.
    """

    @property
    def tasks_limit(self):
        return config.get('ssh_tasks_count')

    def get_new_task(self):
        ssh: SSH = SSH.get_need_checking()
        if ssh:
            return asyncio.create_task(actions.check_ssh_status(ssh))
        else:
            return None


class PortCheckTask(ConcurrentTask):
    """
    Task to check all Port status.
    """

    @property
    def tasks_limit(self):
        return config.get('port_tasks_count')

    def get_new_task(self):
        port: Port = Port.get_need_checking()
        if port is not None:
            return asyncio.create_task(actions.check_port_ip(port))
        else:
            return None


class ConnectSSHToPortTask(SyncTask):
    """
    Task to connect SSH to a Port.
    """

    @db_session(optimistic=False)
    def run(self):
        port: Port = Port.get_need_ssh()
        if not port:
            return None

        unique = config.get('use_unique_ssh')
        ssh: SSH = SSH.get_ssh_for_port(port, unique=unique)
        if not ssh:
            return None

        port.assign_ssh(ssh)
        logger.info(f"Port {port.port_number:<5} -> SSH {ssh.ip:<15} - CONNECTING")
        return asyncio.create_task(actions.connect_ssh_to_port(ssh, port))


class ReconnectNewSSHTask(SyncTask):
    """
    Task to reconnect new SSH to a Port.
    """

    @db_session(optimistic=False)
    def run(self):
        if not config.get('auto_reset_ports'):
            return None

        reset_interval = config.get('port_reset_interval')
        time_expired = datetime.now() - timedelta(seconds=reset_interval)
        ports = Port.get_need_reset(time_expired)
        if ports:
            port_numbers = [str(port.port_number) for port in ports]
            logger.info(f"Resetting ports [{','.join(port_numbers)}]")
            return asyncio.create_task(actions.reset_ports(ports))
        else:
            return None


class SSHStoreDownloadTask(ConcurrentTask):
    """
    Task to automatically get SSH from SSHStore.
    """

    def __init__(self):
        super().__init__()
        self.last_run: Optional[datetime] = None

    @property
    def tasks_limit(self):
        return 1

    @staticmethod
    async def run_get():
        api_key = config.get('sshstore_api_key')
        country = config.get('sshstore_country')
        limit = config.get('sshstore_limit')
        interval = config.get('sshstore_interval')

        # noinspection PyBroadException
        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(
                    f"http://autossh.top/api/txt/{api_key}/{country}/{limit}"
                )
                await actions.insert_ssh_from_file_content(await resp.text())
        except Exception:
            pass
        await asyncio.sleep(interval)

    def get_new_task(self):
        if not config.get('sshstore_enabled'):
            return
        return asyncio.create_task(self.run_get())


class AllTasksRunner(ConcurrentTask):
    """
    Task that run all other tasks in a proper order and manage them.
    """

    def __init__(self):
        super().__init__()
        self.concurrent_tasks: List[Union[ConcurrentTask, CheckTask]] = []
        self.sync_tasks: Deque[SyncTask] = deque()

        for name, cls in globals().items():
            # Ignore unwanted objects/classes
            if not isclass(cls) or isabstract(cls) or cls is type(self):
                continue

            if issubclass(cls, (ConcurrentTask, CheckTask)):
                self.concurrent_tasks.append(cls())
            elif issubclass(cls, SyncTask):
                self.sync_tasks.append(cls())

        self.tasks = [
            asyncio.get_event_loop().create_task(task.run()) for task in self.concurrent_tasks
        ]

    @property
    def tasks_limit(self):
        return 50

    async def stop(self):
        await super().stop()
        for task in self.concurrent_tasks:
            await task.stop()

    def get_new_task(self) -> asyncio.Task:
        count = 0
        while count < len(self.sync_tasks):
            task = self.sync_tasks[0]
            self.sync_tasks.rotate(-1)
            result = task.run()
            if isawaitable(result):
                return result
            count += 1
