import asyncio
import json
import logging
import os.path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers import tasks
from models.database import db
from views import plugins_api, ports_api, settings_api, ssh_api

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(name)s - %(message)s")
app = FastAPI(title="SSHManager by KhanhhNe",
              description="Quản lý SSH chuyên nghiệp và nhanh chóng",
              version=json.load(open('package.json'))['version'])
db.bind('sqlite', 'db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


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


app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.include_router(plugins_api.router, prefix='/api/plugins')
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
