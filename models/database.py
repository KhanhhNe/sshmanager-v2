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
