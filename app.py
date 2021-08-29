import asyncio

from fastapi import FastAPI

from controllers import tasks
from models.database import db
from views import ssh_api

app = FastAPI()
db.bind('sqlite', 'db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


@app.on_event('startup')
async def run_background_tasks():
    asyncio.ensure_future(tasks.ssh_check_task())
    asyncio.ensure_future(tasks.port_check_task())


app.include_router(ssh_api.router, prefix='/api/ssh')
