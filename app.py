import asyncio
import json
import logging
import os.path
import threading

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers import tasks
from models.database import db
from views import plugins_api, ports_api, settings_api, ssh_api

file_logging = logging.FileHandler('debug.log')
file_logging.setLevel(logging.DEBUG)
console_logging = logging.StreamHandler()
console_logging.setLevel(logging.INFO)

logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s] %(name)s - %(message)s",
                    handlers=[file_logging, console_logging])

app = FastAPI(title="SSHManager by KhanhhNe",
              description="Quản lý SSH chuyên nghiệp và nhanh chóng",
              version=json.load(open('package.json'))['version'])
db.bind('sqlite', 'db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

if not os.path.exists('current_thread.txt'):
    open('current_thread.txt', 'w+').write(str(threading.get_ident()))

    # Only register startup and shutdown handler if this thread is the first one
    @app.on_event('startup')
    def startup_tasks():
        tasks.reset_ssh_and_port_status()
        runners = [
            tasks.SSHCheckRunner(),
            tasks.PortCheckRunner(),
            tasks.ConnectSSHToPortRunner()
        ]
        asyncio.ensure_future(asyncio.gather(*[
            runner.run_task() for runner in runners
        ]))
        try:
            os.makedirs('plugins')
        except FileExistsError:
            pass


    @app.on_event('shutdown')
    def shutdown_tasks():
        tasks.kill_child_processes()
        os.remove('current_thread.txt')

app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.include_router(plugins_api.router, prefix='/api/plugins')
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
