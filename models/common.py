from functools import wraps

from pony.orm import ObjectNotFound, db_session, make_proxy

from models import db


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
                    args[ind] = make_proxy(args[ind])

            for key, val in kwargs.items():
                if val and issubclass(type(val), db.Entity):
                    kwargs[key] = make_proxy(val)
        except ObjectNotFound:
            return
        return func(*args, **kwargs)

    return wrapped
