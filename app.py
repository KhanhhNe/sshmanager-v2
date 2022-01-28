import asyncio
import json
import logging
import os.path
import threading

import pony.orm
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers import actions, tasks
from models.database import db
from views import plugins_api, ports_api, settings_api, ssh_api

DB_ENGINE = 'sqlite'
DB_PATH = 'db.sqlite'


def console_logging_filter(record: logging.LogRecord):
    if record.name in ['uvicorn.error', 'asyncio']:
        return False
    return True


def file_logging_filter(record: logging.LogRecord):
    # Pre-filter some annoying logs shown on console
    if not console_logging_filter(record):
        return False
    if record.name in ['websockets.protocol', 'websockets.server']:
        return False
    return True


def is_main_child_thread():
    return not os.path.exists('current_thread.txt')


def register_main_child_thread():
    open('current_thread.txt', 'w+').write(str(ident))


def unregister_main_child_thread():
    os.remove('current_thread.txt')


app = FastAPI(title="SSHManager by KhanhhNe",
              description="Quản lý SSH chuyên nghiệp và nhanh chóng",
              version=json.load(open('package.json'))['version'])

# Configure loggings
if is_main_child_thread():
    console_logging = logging.StreamHandler()
    file_logging = logging.FileHandler('debug.log', mode='w')
else:
    console_logging = logging.StreamHandler()
    file_logging = logging.FileHandler('debug.log', mode='a')

console_logging.setLevel(logging.INFO)
console_logging.addFilter(console_logging_filter)
file_logging.setLevel(logging.DEBUG)
file_logging.addFilter(file_logging_filter)

logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s] %(name)s %(levelname)s - %(message)s",
                    handlers=[file_logging, console_logging],
                    force=True)

# Only init for main child thread
if is_main_child_thread():
    # noinspection PyUnresolvedReferences
    try:
        db.bind(DB_ENGINE, DB_PATH, create_db=True)
        db.generate_mapping(create_tables=True)
    except pony.orm.dbapiprovider.OperationalError:
        os.remove(DB_PATH)
        db.bind(DB_ENGINE, DB_PATH, create_db=True)
        db.generate_mapping(create_tables=True)

    ident = threading.get_ident()
    register_main_child_thread()
    task: asyncio.Task


    # Only register handlers if this is the main thread
    @app.on_event('startup')
    def startup_tasks():
        actions.reset_ssh_and_port_status()
        runners = [
            tasks.SSHCheckRunner(),
            tasks.PortCheckRunner(),
            tasks.ConnectSSHToPortRunner()
        ]
        global task
        task = asyncio.ensure_future(asyncio.gather(*[
            runner.run_task() for runner in runners
        ]))
        os.makedirs('plugins', exist_ok=True)


    @app.on_event('shutdown')
    async def shutdown_tasks():
        task.cancel()
        actions.kill_child_processes()
        unregister_main_child_thread()

# Routers
app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.include_router(plugins_api.router, prefix='/api/plugins')
app.mount('/api/plugins/js', StaticFiles(directory='plugins', check_dir=False))
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
