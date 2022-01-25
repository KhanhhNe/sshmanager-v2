import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List

from pony.orm import db_session

import config
from controllers import actions
from models.port_models import Port
from models.ssh_models import SSH

logger = logging.getLogger('Tasks')


class TaskRunner(ABC):
    def __init__(self):
        self.tasks: List[asyncio.Task] = []

    @property
    @abstractmethod
    def tasks_limit(self):
        raise NotImplementedError

    @abstractmethod
    def get_new_task(self):
        """Get a task to add to the runner. Return either a Coroutine or Task"""
        raise NotImplementedError

    async def run_task(self):
        while True:
            while len(self.tasks) < self.tasks_limit:
                new_task = self.get_new_task()
                if new_task is not None:
                    self.tasks.append(new_task)
                else:
                    break

            # Await done tasks
            await asyncio.gather(*[task for task in self.tasks if task.done()])

            # Remove those tasks, keeping only pending ones
            self.tasks = [task for task in self.tasks if not task.done()]
            await asyncio.sleep(0)


class SSHCheckRunner(TaskRunner):
    @property
    def tasks_limit(self):
        conf = config.get_config()
        return conf.getint('SSH', 'tasks_count')

    def get_new_task(self):
        with db_session:
            not_checked = SSH.select().filter(
                lambda obj: obj.is_checking is False)
            ssh = not_checked \
                .filter(lambda obj: obj.last_checked is None) \
                .for_update().first()
            if ssh is None:
                ssh = not_checked \
                    .order_by(lambda obj: obj.last_checked) \
                    .for_update().first()
            if ssh is None:
                return None
            ssh.is_checking = True
            return asyncio.ensure_future(actions.check_ssh_status(ssh))


class PortCheckRunner(TaskRunner):
    @property
    def tasks_limit(self):
        conf = config.get_config()
        return conf.getint('PORT', 'tasks_count')

    def get_new_task(self):
        with db_session:
            not_checked = Port.select() \
                .filter(lambda obj: not obj.is_checking) \
                .filter(lambda obj: obj.ssh is not None)
            port = not_checked \
                .filter(lambda obj: obj.last_checked is None) \
                .for_update().first()
            if port is None:
                port = not_checked \
                    .order_by(lambda obj: obj.last_checked) \
                    .for_update().first()
            if port is None:
                return None
            else:
                port.is_checking = True
            return asyncio.ensure_future(actions.check_port_ip(port))


class ConnectSSHToPortRunner(TaskRunner):
    @property
    def tasks_limit(self):
        conf = config.get_config()
        return conf.getint('PORT', 'tasks_count')

    def get_new_task(self):
        with db_session:
            port = Port.select(lambda p: p.ssh is None) \
                .for_update(skip_locked=True).first()
            if port is None:
                return None
            ssh = SSH.select(lambda s: s.is_live and s.port is None) \
                .for_update(skip_locked=True).first()
            if ssh is None:
                return None
            port.ssh = ssh
            return asyncio.ensure_future(actions.connect_ssh_to_port(ssh, port))
