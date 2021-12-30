import json
from typing import List

from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRouter
from pony.orm import db_session

import utils
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


@router.get('/proxies/')
def get_proxies_string(full_url: str = None):
    """
    Get proxies information (to integrate with other tools), one per line
    :param full_url: If it is true, returns full proxy URL
    (<protocol>://<ip>:<port>), otherwise returns only <ip>:<port>
    :return:
    """
    results = []
    with db_session:
        for port in Port.select():
            info_str = f"{utils.get_ipv4_address()}:{port.port}"
            if full_url:
                results.append(f"socks5://{info_str}")
            else:
                results.append(info_str)
    return PlainTextResponse('\n'.join(results))
