import asyncio
import json
import logging
import os.path
import threading
import time

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from pony import orm

from controllers import actions
from controllers.tasks import AllTasksRunner
from models import db
from views import ports_api, settings_api, ssh_api

DB_ENGINE = 'sqlite'
DB_PATH = 'db.sqlite'


def logging_filter(record: logging.LogRecord):
    if 'Accept failed on a socket' in record.msg:
        # INFO level messages
        return False
    elif record.levelname == 'DEBUG' and 'websockets' in record.name:
        # DEBUG level messages
        return False
    elif record.levelname == 'DEBUG' and 'charset_normalizer' in record.name:
        # charset_normalizer messages
        return False
    else:
        # Other cases
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

if not os.environ.get('DEBUG'):
    console_logging.setLevel(logging.INFO)
else:
    console_logging.setLevel(logging.DEBUG)
file_logging.setLevel(logging.DEBUG)

console_logging.addFilter(logging_filter)
file_logging.addFilter(logging_filter)

logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s] %(name)s %(levelname)s - %(message)s",
                    handlers=[file_logging, console_logging],
                    force=True)

# noinspection PyUnresolvedReferences
db.bind(DB_ENGINE, DB_PATH, create_db=True)
try:
    db.generate_mapping(create_tables=True)
except orm.OperationalError:
    os.remove(DB_PATH)
    db.generate_mapping(create_tables=True)

# Only init for main child thread
if is_main_child_thread():
    ident = threading.get_ident()
    register_main_child_thread()
    runner = AllTasksRunner()

    # Only register handlers if this is the main thread
    @app.on_event('startup')
    def startup_tasks():
        actions.reset_old_status()
        asyncio.ensure_future(runner.run())
        os.makedirs('plugins', exist_ok=True)


    @app.on_event('shutdown')
    async def shutdown_tasks():
        await runner.stop()
        actions.kill_child_processes()
        unregister_main_child_thread()


# Middlewares
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger('Request')
    start_time = time.perf_counter()

    response: Response = await call_next(request)

    process_time = "{:5.2f}".format((time.perf_counter() - start_time) * 1000)
    query = request.url.query
    if query:
        query = '?' + query
    logger.info(f"{request.method} {response.status_code} ({process_time}ms) - "
                f"{request.url.path}{query}")

    return response


# Routers
app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
