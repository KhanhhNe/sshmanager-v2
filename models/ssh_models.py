from datetime import datetime

from pony.orm import *

from .database import db


class SSH(db.Entity):
    """
    Store SSH information
    """
    ip = Required(str)
    username = Optional(str)
    password = Optional(str)
    is_live = Required(bool, default=False)
    port = Optional('Port')
    is_checking = Required(bool, default=False)
    last_checked = Optional(datetime)
