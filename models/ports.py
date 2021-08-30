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
    if next_port:
        next_port.is_checking = True
        return next_port
    else:
        return None


@db_session
def update_port_status(updated_port: Port, *, is_usable=None):
    """
    Update port status. Will update port.last_checked if is_usable is specified
    and will remove associated SSH if is_usable is False.
    :param updated_port:
    :param is_usable:
    """
    port: Port = Port[updated_port.id]
    if not port:
        return

    if is_usable is not None:
        port.last_checked = datetime.now()
    port.is_usable = is_usable
    if not port.is_usable:
        port.ssh = None
