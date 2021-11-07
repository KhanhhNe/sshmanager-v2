import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import psutil
from pony.orm import ObjectNotFound, db_session

import config
from controllers import putty_controllers
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
            while len(self.tasks) < self.tasks_limit():
                new_task = self.get_new_task()
                if new_task is not None:
                    self.tasks.append(asyncio.ensure_future(new_task))
                else:
                    break
            # Remove done tasks
            self.tasks = [task for task in self.tasks if not task.done()]
            await asyncio.sleep(1)


class SSHCheckRunner(TaskRunner):
    def tasks_limit(self):
        conf = config.get_config()
        tasks_count = conf.getint('SSH', 'tasks_count')
        workers_count = conf.getint('WEB', 'workers')
        return tasks_count // workers_count

    def get_new_task(self):
        with db_session:
            not_checked = SSH.select().filter(
                lambda obj: obj.is_checking is False)
            ssh = not_checked \
                .filter(lambda obj: obj.last_checked is None) \
                .first()
            if ssh is None:
                ssh = not_checked \
                    .order_by(lambda obj: obj.last_checked) \
                    .first()
            if ssh is None:
                return None

            ssh.is_checking = True
            return check_ssh_status(ssh)


class PortCheckRunner(TaskRunner):
    def tasks_limit(self):
        conf = config.get_config()
        tasks_count = conf.getint('PORT', 'tasks_count')
        workers_count = conf.getint('WEB', 'workers')
        return tasks_count // workers_count

    def get_new_task(self):
        with db_session:
            not_checked = Port.select() \
                .filter(lambda obj: not obj.is_checking) \
                .filter(lambda obj: obj.ssh is not None)
            port = not_checked \
                .filter(lambda obj: obj.last_checked is None) \
                .first()
            if port is None:
                port = not_checked \
                    .order_by(lambda obj: obj.last_checked) \
                    .first()
            if port is not None:
                port.is_checking = True
                return check_port_ip(port)
            else:
                return None


class ConnectSSHToPortRunner(TaskRunner):
    def tasks_limit(self):
        conf = config.get_config()
        tasks_count = conf.getint('PORT', 'tasks_count')
        workers_count = conf.getint('WEB', 'workers')
        return tasks_count // workers_count

    def get_new_task(self):
        with db_session:
            port = Port.select(lambda p: not p.ssh).first()
            if not port:
                return None
            ssh = SSH.select(lambda s: s.is_live and not s.port).first()
            if not ssh:
                return None
            port.ssh = ssh
            return connect_ssh_to_port(ssh, port)


async def check_ssh_status(ssh: SSH):
    """
    Check for SSH live/die status and save to db
    :param ssh: Target SSH
    """
    is_live = await putty_controllers.verify_ssh(ssh.ip,
                                                 ssh.username,
                                                 ssh.password)

    with db_session:
        try:
            ssh: SSH = SSH[ssh.id]
        except ObjectNotFound:
            return

        ssh.last_checked = datetime.now()
        ssh.is_live = is_live
        ssh.is_checking = False


async def check_port_ip(port: Port):
    """
    Check for port's external IP and save to db
    :param port: Target port
    """
    ip = await putty_controllers.get_proxy_ip(port.proxy_address)

    with db_session:
        try:
            port: Port = Port[port.id]
        except ObjectNotFound:
            return

        if not ip and port.is_connected_to_ssh:
            port.ssh = None
            port.is_connected_to_ssh = False

        port.ip = ip
        port.last_checked = datetime.now()
        port.is_checking = False


async def connect_ssh_to_port(ssh: SSH, port: Port):
    """
    Connect SSH to port and save to db
    :param port: Target port
    :param ssh: SSH to perform port-forwarding
    """
    try:
        await putty_controllers.connect_ssh(ssh.ip, ssh.username, ssh.password,
                                            port=port.port)
        is_connected = True
        logger.info(f"Port {port.port} connected to SSH {ssh.ip}")
    except putty_controllers.PuttyError:
        is_connected = False
        logger.info(f"Port {port.port} failed to connect to SSH {ssh.ip}")

    with db_session:
        try:
            port: Port = Port[port.id]
            ssh: SSH = SSH[ssh.id]
        except ObjectNotFound:
            return

        if is_connected:
            port.is_connected_to_ssh = True
            port.ip = ssh.ip
        else:
            port.ssh = None
            ssh.is_live = False


def reset_ssh_and_port_status():
    """
    Reset attribute is_checking of Port and SSH to False on startup
    """
    with db_session:
        for ssh in SSH.select():
            ssh.is_checking = False
        for port in Port.select():
            port.is_checking = False
            port.ip = ''
            port.ssh = None
            port.is_connected_to_ssh = False


def kill_child_processes():
    """
    Kill all child processes started by the application
    """
    process = psutil.Process()
    children: List[psutil.Process] = process.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children)
