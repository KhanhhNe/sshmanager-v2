from typing import List

from fastapi.routing import APIRouter
from pony.orm import db_session

from models import port_models
from models.io_models import PortIn, PortOut

router = APIRouter()


@router.get('/')
def get_all_ports():
    """
    Get all ports from database.
    """
    with db_session:
        ports = port_models.Port.select()[:].to_list()
    return [PortOut.from_orm(port) for port in ports]


@router.post('/')
def add_ports(port_list: List[PortIn]):
    """
    Add port to database
    :param port_list: Ports to add
    """
    with db_session:
        for port in port_list:
            if not port_models.Port.get(**port.dict()):
                Port(**port.dict())
    return {}


@router.delete('/')
def delete_port(port_list: List[PortIn]):
    """
    Remove a list of port from the database.
    """
    with db_session:
        for port in port_list:
            port_obj = port_models.Port.get(**port.dict())
            if port_obj:
                port_obj.delete()
    return {}
