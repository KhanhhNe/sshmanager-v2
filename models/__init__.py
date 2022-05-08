from datetime import datetime
from functools import wraps

from pony.orm import *

import utils
from .database import db


def auto_renew_objects(func):
    """
    Decorator to ensure objects are got from current db_session before executing
    the function.
    """

    @wraps(func)
    @db_session(optimistic=False)
    def wrapped(*args, **kwargs):
        args = list(args)
        try:
            for ind, arg in enumerate(args):
                if arg and issubclass(type(arg), db.Entity):
                    args[ind] = type(arg)[arg.id]

            for key, val in kwargs.items():
                if val and issubclass(type(val), db.Entity):
                    kwargs[key] = type(val)[val.id]
        except ObjectNotFound:
            return
        return func(*args, **kwargs)

    return wrapped


class CheckingSupported(db.Entity):
    """
    Support for checking parameters and selecting.
    """
    is_checking = Required(bool, default=False)
    last_checked = Optional(datetime)

    # noinspection PyTypeChecker
    @classmethod
    @auto_renew_objects
    def get_need_checking(cls, begin=True):
        """
        Get a new object that need checking. Will call begin_checking() if
        begin=True.

        :param begin: If it is True, call begin_checking() on received object
        :return: Object that need checking if any, None otherwise
        """
        query = select(o for o in cls if not o.is_checking)
        obj = query.filter(lambda o: o.last_checked is None).first()
        if obj is None:
            obj = query.order_by(cls.last_checked).first()
        if begin and obj is not None:
            cls.begin_checking(obj)
        return obj

    @classmethod
    @auto_renew_objects
    def begin_checking(cls, obj):
        """
        Start the checking process (set checking-related flags in database).

        :param obj: Object
        """
        obj.is_checking = True

    @classmethod
    @auto_renew_objects
    def end_checking(cls, obj, **kwargs):
        """
        Stop checking and update object's values into database using the keyword
        arguments.

        :param obj: Object
        :param kwargs: Updating values
        """
        for key, value in kwargs.items():
            obj.__setattr__(key, value)
        obj.is_checking = False
        obj.last_checked = datetime.now()

    @auto_renew_objects
    def reset_status(self):
        """
        Reset all object's status.
        """
        self.is_checking = False
        self.last_checked = None


class SSH(CheckingSupported):
    """
    Store SSH information.
    """
    ip = Required(str)
    username = Optional(str)
    password = Optional(str)
    is_live = Required(bool, default=False)
    port = Optional('Port')
    used_ports: Set = Set('Port')

    @property
    def is_usable(self):
        return self.is_live and self.port is None

    @classmethod
    def get_ssh_for_port(cls, port: 'Port', unique=True):
        """
        Get a usable SSH for provided Port. Will not get one that was used by
        that Port before if unique=True.

        :param port: Port
        :param unique: True if the SSH cannot be used before by Port
        :return: Usable SSH for Port
        """
        query = cls.select(lambda s: s.is_usable)
        if unique:
            query = query.filter(lambda s: s.id not in port.used_ssh_list.id)
        result = query.random(1)
        if result:
            return result[0]
        else:
            return None

    @auto_renew_objects
    def reset_status(self):
        super().reset_status()


class Port(CheckingSupported):
    """
    Store port information.
    """
    port_number = Required(int, unique=True)
    ssh = Optional(SSH)
    external_ip = Optional(str)  # External IP after proxying through port
    used_ssh_list: Set = Set(SSH, reverse='used_ports')
    time_connected = Optional(datetime)

    @property
    def proxy_address(self):
        return f"socks5://{utils.get_ipv4_address()}:{self.port_number}"

    @auto_renew_objects
    def need_reset(self, time_expired: datetime):
        return self.ssh is not None and self.time_connected < time_expired

    @classmethod
    def get_need_reset(cls, time_expired: datetime):
        return cls.select(lambda p: p.need_reset(time_expired))[:]

    @property
    @auto_renew_objects
    def need_ssh(self):
        return self.ssh is None

    @property
    def is_connected(self):
        return self.time_connected is not None

    @is_connected.setter
    @auto_renew_objects
    def is_connected(self, value: bool):
        if value is True:
            self.time_connected = datetime.now()
            self.used_ssh_list.add(self.ssh)
        else:
            self.time_connected = None

    @classmethod
    def get_need_ssh(cls):
        return cls.select(lambda s: s.need_ssh).first()

    @classmethod
    @auto_renew_objects
    def end_checking(cls, obj: 'Port', **kwargs):
        super().end_checking(obj, **kwargs)
        if (
                obj.is_connected and
                obj.external_ip != obj.ssh.ip
        ):
            obj.disconnect_ssh(obj.ssh)

    @auto_renew_objects
    def assign_ssh(self, ssh: SSH):
        self.ssh = ssh
        self.is_connected = False

    @auto_renew_objects
    def disconnect_ssh(self, ssh: SSH, remove_from_used=False):
        self.assign_ssh(None)
        if remove_from_used:
            self.used_ssh_list.remove(ssh)

    @auto_renew_objects
    def reset_status(self):
        super().reset_status()
        self.external_ip = ''
        self.ssh = None
        self.time_connected = None
        self.used_ssh_list.clear()
