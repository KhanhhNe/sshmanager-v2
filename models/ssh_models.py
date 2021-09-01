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
    port = Optional('Port')
    is_checking = Required(bool, default=False)
    last_checked = Required(datetime, default=datetime(1000, 1, 1))
