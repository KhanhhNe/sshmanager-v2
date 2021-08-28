from datetime import datetime
from typing import List

from pony.orm import *

from .database import db
from .io_models import SSHInfo


class SSH(db.Entity):
    """
    Store SSH information
    """
    ip = Required(str)
    username = Required(str)
    password = Required(str)
    is_live = Required(bool, default=False)
    port = Optional('Port')
    is_using = Required(bool, default=False)
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))

    @db_session
    def __enter__(self):
        self.is_checking = True
        return self

    @db_session
    def __exit__(self, *_):
        # SSH is get for checking -> update last_checked
        if self.is_checking:
            self.last_checked = datetime.now()
            self.is_checking = False


@db_session
def get_ssh_to_check():
    """
    Get a SSH to check for status. This function will set SSH is_checking to True
    :return:
    """
    next_ssh: SSH = SSH \
        .select() \
        .filter(lambda ssh: ssh.is_checking is False) \
        .order_by(lambda ssh: ssh.last_checked) \
        .first()
    next_ssh.is_checking = True
    return next_ssh


@db_session
def add_ssh(ssh_list: List[SSHInfo]):
    for ssh in ssh_list:
        if not SSH.get(**ssh.dict()):
            SSH(**ssh.dict())  # Add new SSH if it isn't added yet
