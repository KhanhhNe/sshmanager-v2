import asyncio
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import tasks
from models.database import db
from views import ports_api, ssh_api

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(name)s - %(message)s")
app = FastAPI(title="SSHManager by KhanhhNe",
              description="Quản lý SSH chuyên nghiệp và nhanh chóng",
              version="2.0.1")
db.bind('sqlite', 'db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


@app.on_event('startup')
def startup_tasks():
    tasks.reset_ssh_and_port_status()
    asyncio.ensure_future(tasks.main_task())


@app.on_event('shutdown')
def shutdown_tasks():
    tasks.kill_child_processes()


app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.mount('/', StaticFiles(directory='dist', html=True))
