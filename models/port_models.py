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
    ip = Optional(str)  # External IP after proxying through port
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))

    @property
    def proxy_address(self):
        return f"socks5://{utils.get_ipv4_address()}:{self.port}"
