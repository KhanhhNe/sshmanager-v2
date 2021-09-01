import os
import signal

from pony.orm import *

from .database import db


class ProxyProcess(db.Entity):
    """
    Store SSH connecting processes for conveniently managing and killing them
    """
    pid = Required(int, unique=True)
    port = Required(int, unique=True)

    def kill_process(self):
        os.kill(self.pid, signal.SIGTERM)


@db_session
def add_proxy_process(pid: int, port: int):
    """
    Add a proxy process to database
    :param pid:
    :param port:
    """
    ProxyProcess(pid=pid, port=port)
    commit()


@db_session
def kill_proxy_process(pid: int):
    """
    Kill a proxy process
    :param pid:
    """
    # noinspection PyTypeChecker
    process: ProxyProcess = ProxyProcess.get(pid=pid)
    if process:
        process.kill_process()
        ProxyProcess[process.id].delete()
        commit()
