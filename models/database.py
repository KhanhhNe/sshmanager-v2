import os

from pony import orm
from pony.orm import Database


def setup_debug_db_session():
    import threading
    import pyinstrument
    from pony.orm.core import DBSessionContextManager

    class DebugDBSession(DBSessionContextManager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.ps = {}

        def __enter__(self):
            super().__enter__()
            self.ps[threading.get_ident()] = pyinstrument.Profiler(async_mode='disabled')
            self.ps[threading.get_ident()].start()

        def __exit__(self, *args):
            ident = threading.get_ident()
            if self.ps.get(ident):
                self.ps[ident].stop()
                if self.ps[ident].last_session.duration > 0.5:
                    self.ps[ident].print()
                self.ps[ident].reset()
            super().__exit__(*args)

    orm.db_session = DebugDBSession()


if os.getenv('DEBUG_DB', False):
    setup_debug_db_session()

DB_ENGINE = 'sqlite'
DB_PATH = os.path.join(os.getcwd(), 'data', 'db.sqlite')

db = Database()


def init_db():
    if db.provider is not None:
        return

    db.bind(DB_ENGINE, DB_PATH, create_db=True)
    try:
        db.generate_mapping(create_tables=True)
    except orm.OperationalError:
        os.remove(DB_PATH)
        db.generate_mapping(create_tables=True)

    from .models import SSH, Port

    with db.set_perms_for(SSH):
        orm.perm('view', group='anybody')
    with db.set_perms_for(Port):
        orm.perm('view', group='anybody')
