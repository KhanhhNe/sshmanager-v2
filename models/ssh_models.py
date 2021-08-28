from datetime import datetime

from pony.orm import *

from .database import db


class SSH(db.Entity):
    """
    Store SSH information
    """
    ip = Required(str)
    username = Required(str)
    password = Required(str)
    is_live = Required(bool, default=False)
    is_using = Required(bool, default=False)
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))

    def update_status(self, *, is_live=None, is_using=None):
        """
        Update SSH status. If is_live is updated, the SSH's last_checked will be updated too.
        :param is_live:
        :param is_using:
        """
        if is_live is not None:
            self.is_live = is_live
            self.last_checked = datetime.now()

        if is_using is not None:
            self.is_using = is_using


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
    commit()
    return next_ssh


@db_session
def update_ssh_status(ssh: SSH, is_live):
    """
    Update SSH status after check. This function will set SSH is_checking to False
    :param ssh:
    :param is_live:
    """
    ssh.is_checking = False
    ssh.update_status(is_live=is_live)
    commit()
