import os

from pony import orm
from pony.orm import Database

DB_ENGINE = 'sqlite'
DB_PATH = '../data/db.sqlite'

db = Database()


def init_db():
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


def generate_mappings():
    db.bind(DB_ENGINE, DB_PATH)
    db.generate_mapping()
