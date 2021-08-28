from datetime import datetime

from pony.orm import *

import utils
from .database import db
from .ssh_models import SSH


class Port(db.Entity):
    """
    Store port information
    """
    port = Required(int)
    ssh = Optional(SSH)
    is_usable = Required(bool, default=False)
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))

    @property
    def proxy_address(self):
        return f"socks5://{utils.get_ipv4_address()}:{self.port}"

    @db_session
    def __enter__(self):
        self.is_checking = True
        commit()
        return self

    @db_session
    def __exit__(self, *_):
        if self.is_checking:
            self.last_checked = datetime.now()
            self.is_checking = False

        commit()


@db_session
def get_port_to_check():
    """
    Check port for connectivity. Will set is_checking to True before return
    :return:
    """
    next_port: Port = Port \
        .select() \
        .filter(lambda port: port.is_checking is False) \
        .order_by(lambda port: port.last_checked) \
        .first()
    next_port.is_checking = True
    commit()
    return next_port
