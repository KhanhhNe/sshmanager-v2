import asyncio

from fastapi import FastAPI

import tasks
from models.database import db
from views import ports_api, ssh_api

app = FastAPI()
db.bind('sqlite', 'db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


@app.on_event('startup')
def startup_tasks():
    asyncio.ensure_future(tasks.ssh_check_task())
    asyncio.ensure_future(tasks.port_check_task())
    asyncio.ensure_future(tasks.port_connect_task())
    tasks.reset_ssh_and_port_status()


@app.on_event('shutdown')
def shutdown_tasks():
    tasks.kill_child_processes()


app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
