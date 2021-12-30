import json
from typing import List

from fastapi.routing import APIRouter
from pony.orm import db_session

from models.io_models import PortIn, PortOut
from models.port_models import Port
from views import update_websocket

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
@update_websocket
def get_ports_json():
    return [json.loads(p.json()) for p in get_all_ports()]


@router.post('/')
def add_ports(port_list: List[PortIn]):
    """
    Add ports to database
    """
    with db_session:
        for port in port_list:
            if not Port.get(**port.dict()):
                Port(**port.dict())
    return {}


@router.delete('/')
def delete_ports(port_list: List[PortIn]):
    """
    Remove a list of ports from the database.
    """
    with db_session:
        for port in port_list:
            port_obj = Port.get(**port.dict())
            if port_obj:
                port_obj.delete()
    return {}


@router.put('/')
def reset_ports_ssh(port_list: List[PortIn]):
    """
    Reset assigned SSH of ports
    """
    port_numbers = [port.port for port in port_list]
    with db_session:
        for port in Port.select(lambda p: p.port in port_numbers):
            port.ssh = None
            port.time_connected = None
    return {}
