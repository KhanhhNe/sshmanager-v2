import asyncio
import json
from typing import List

from fastapi.routing import APIRouter
from fastapi.websockets import WebSocket
from pony.orm import db_session

from models.database import db
from models.io_models import PortIn, PortOut
from models.port_models import Port

router = APIRouter()


@router.get('/')
def get_all_ports():
    """
    Get all ports from database.
    """
    with db_session:
        ports = Port.select()[:].to_list()
        return [PortOut.from_orm(port) for port in ports]


@router.websocket('/')
async def update_information(websocket: WebSocket):
    await websocket.accept()
    total_slept = float('inf')

    while True:
        if total_slept >= 60 or not db.last_sql.startswith('SELECT'):
            await websocket.send_json([
                json.loads(p.json()) for p in get_all_ports()
            ])
            total_slept = 0
        await asyncio.sleep(0.5)
        total_slept += 0.5


@router.post('/')
def add_ports(port_list: List[PortIn]):
    """
    Add port to database
    :param port_list: Ports to add
    """
    with db_session:
        for port in port_list:
            if not Port.get(**port.dict()):
                Port(**port.dict())
    return {}


@router.delete('/')
def delete_port(port_list: List[PortIn]):
    """
    Remove a list of port from the database.
    """
    with db_session:
        for port in port_list:
            port_obj = Port.get(**port.dict())
            if port_obj:
                port_obj.delete()
    return {}
