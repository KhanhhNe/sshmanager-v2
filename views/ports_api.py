import json
from typing import List

from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRouter
from pony.orm import db_session

import config
from controllers.actions import reset_ports
from models import Port
from models.io_models import PortIn, PortOut
from views import update_websocket

router = APIRouter()


@router.get('/')
@db_session
def get_all_ports():
    """
    Get all ports from database.
    """
    ports = Port.select()[:].to_list()
    return [PortOut.from_orm(port) for port in ports]


@router.websocket('/')
@update_websocket
def get_ports_json():
    return [json.loads(p.json()) for p in get_all_ports()]


@router.post('/')
@db_session
def add_ports(port_list: List[PortIn]):
    """
    Add ports to database
    """
    results = []
    for port in port_list:
        if not Port.get(**port.dict()):
            p = Port(**port.dict())
            results.append(p)
    return [PortOut.from_orm(p) for p in results]


# TODO change to requiring Port numbers only
@router.delete('/')
@db_session
def delete_ports(port_list: List[PortIn]):
    """
    Remove a list of ports from the database.
    """
    deleted = 0
    for port in port_list:
        port_obj = Port.get(**port.dict())
        if port_obj:
            port_obj.delete()
            deleted += 1
    return deleted


# TODO change to requiring Port numbers only
@router.put('/')
async def reset_ports_ssh(port_list: List[PortIn], delete_ssh=False):
    """
    Reset assigned SSH of Ports.

    :return: Reset Ports (excluding non-existing Ports)
    """
    ports = []
    with db_session:
        for port in port_list:
            if Port.exists(port_number=port.port_number):
                ports.append(Port.get(port_number=port.port_number))
    unique = config.get('use_unique_ssh')
    await reset_ports(ports, unique=unique, delete_ssh=delete_ssh)
    with db_session:
        return [PortOut.from_orm(Port[p.id]) for p in ports]


@router.get('/proxies/')
@db_session
def get_proxies_string(full_url: str = None):
    """
    Get proxies information (to integrate with other tools), one per line

    :param full_url: If it is true, returns full proxy URL
    (<protocol>://<ip>:<port>), otherwise returns only <ip>:<port>
    :return:
    """
    results = []
    for port in Port.select():
        info_str = port.proxy_address
        if full_url:
            results.append(f"socks5://{info_str}")
        else:
            results.append(info_str)
    return PlainTextResponse('\n'.join(results))
