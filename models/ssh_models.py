from datetime import datetime
from typing import List

from pony.orm import *

from .database import db
from .io_models import SSHIn


class SSH(db.Entity):
    """
    Store SSH information
    """
    ip = Required(str)
    username = Required(str)
    password = Required(str)
    is_live = Required(bool, default=False)
    port = Optional('Port')
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))


@db_session
def get_ssh_to_check():
    """
    Get a SSH to check for status. Will set SSH is_checking to True
    :return:
    """
    next_ssh: SSH = SSH \
        .select() \
        .filter(lambda ssh: ssh.is_checking is False) \
        .order_by(lambda ssh: ssh.last_checked) \
        .first()
    if next_ssh:
        next_ssh.is_checking = True
        return next_ssh
    else:
        return None


@db_session
def update_ssh_status(updated_ssh: SSH, *, is_live=None):
    """
    Update SSH status. Will update SSH.last_checked if is_live is specified
    :param updated_ssh:
    :param is_live:
    """
    ssh: SSH = SSH[updated_ssh.id]
    if not ssh:
        return

    if is_live is not None:
        ssh.last_checked = datetime.now()
    ssh.is_live = is_live


@db_session
def add_ssh(ssh_list: List[SSHIn]):
    """
    Add a list of SSH to database
    :param ssh_list:
    """
    for ssh in ssh_list:
        if not SSH.get(**ssh.dict()):
            SSH(**ssh.dict())  # Add new SSH


@db_session
def remove_ssh(ssh_list: List[SSHIn]):
    """
    Remove SSH in list from database
    :param ssh_list:
    """
    for ssh in ssh_list:
        ssh_obj = SSH.get(**ssh.dict())
        if ssh_obj:
            ssh_obj.delete()


@db_session
def get_all_ssh() -> List[SSH]:
    """
    Get all SSH in database
    :return:
    """
    return SSH.select()[:].to_list()
