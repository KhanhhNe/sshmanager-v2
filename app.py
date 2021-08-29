import asyncio

from fastapi import FastAPI

from controllers import tasks
from views import ssh_api

app = FastAPI()


@app.on_event('startup')
async def run_background_tasks():
    asyncio.ensure_future(tasks.ssh_check_task())
    asyncio.ensure_future(tasks.port_check_task())


app.include_router(ssh_api.router, prefix='/api/ssh')
