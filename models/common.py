from functools import wraps

from pony.orm import ObjectNotFound, db_session

from models import db


def auto_renew_objects(func):
    """
    Decorator to ensure objects are got from current db_session before executing
    the function.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        with db_session(optimistic=False):
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
