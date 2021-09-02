import asyncio
import json
from typing import List

from fastapi.routing import APIRouter
from fastapi.websockets import WebSocket
from pony.orm import db_session

from models.database import db
from models.io_models import SSHIn, SSHOut
from models.ssh_models import SSH

router = APIRouter()


@router.get('/')
def get_all_ssh():
    """
    Get all SSH from database.
    """
    with db_session:
        ssh_list = SSH.select()[:].to_list()
        return [SSHOut.from_orm(ssh) for ssh in ssh_list]


@router.websocket('/')
async def update_information(websocket: WebSocket):
    await websocket.accept()
    total_slept = float('inf')

    while True:
        if total_slept >= 60 or not db.last_sql.startswith('SELECT'):
            await websocket.send_json([
                json.loads(s.json()) for s in get_all_ssh()
            ])
            total_slept = 0
        await asyncio.sleep(0.5)
        total_slept += 0.5


@router.post('/')
def add_ssh(ssh_list: List[SSHIn]):
    """
    Add a list of SSH into the database. The list will be checked automatically
    when a runner got to it.
    """
    with db_session:
        for ssh in ssh_list:
            if not SSH.get(**ssh.dict()):
                SSH(**ssh.dict())  # Add new SSH
    return {}


@router.delete('/')
def delete_ssh(ssh_list: List[SSHIn]):
    """
    Remove a list of SSH from the database.
    """
    with db_session:
        for ssh in ssh_list:
            ssh_obj = SSH.get(**ssh.dict())
            if ssh_obj:
                ssh_obj.delete()
    return {}
