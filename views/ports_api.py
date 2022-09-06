from typing import List

from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRouter
from pony.orm import db_session

import config
from controllers.actions import reset_ports
from models import Port, SSH
from models.io_models import PortIn, PortOut
from views.websockets import websocket_auto_update_endpoint

router = APIRouter()


@router.get('', response_model=List[PortOut])
@db_session(optimistic=False)
def get_all_ports():
    """
    Lấy thông tin các Port có trong dữ liệu.

    :return: Danh sách thông tin SSH
    """
    ports = Port.select()[:].to_list()
    return [PortOut.from_orm(port) for port in ports]


@router.post('', response_model=List[PortOut])
@db_session
def add_ports(ports: List[PortIn]):
    """
    Tạo Port.

    :param ports: Danh sách thông tin Port muốn

    :return: Thông tin Port sau khi tạo
    """
    results = []
    for port in ports:
        if not Port.exists(**port.dict()):
            results.append(Port(**port.dict()))

    return [PortOut.from_orm(p) for p in results]


@router.delete('', response_model=int)
@db_session
def delete_ports(port_numbers: List[int]):
    """
    Xoá SSH.

    :param port_numbers: Số port local của các Port muốn xoá (1024-65353)

    :return: Số lượng Port đã xoá
    """
    return Port.select(lambda port: port.port_number in port_numbers).delete(bulk=True)


@router.put('', response_model=int)
async def reset_ports_ssh(port_numbers: List[int], delete_ssh=False):
    """
    Đổi IP (SSH) cho Port.

    :param port_numbers: Số port local của các Port muốn xoá (1024-65353)

    :param delete_ssh: Xoá SSH hiện tại của các Port ra khỏi dữ liệu

    :return: Thông tin Port sau khi reset
    """
    with db_session:
        ports = Port.select().where(Port.port_number.in_(port_numbers))

    await reset_ports(ports, unique=config.get('use_unique_ssh'), delete_ssh=delete_ssh)

    with db_session:
        return [PortOut.from_orm(Port[port.id]) for port in ports]


@router.get('/proxies', response_model=str)
@db_session
def get_proxies_string(full_url: str = None):
    """
    Lấy thông tin proxy (chủ yếu dùng để tích hợp với các tool khác). Thông tin sẽ hiển thị theo dạng đã chọn, với mỗi
    dòng là một proxy

    :param full_url: Trả về thông tin proxy dạng full (<protocol://<ip>:<port>) nếu True, trả về <ip>:<port> nếu False

    :return: Thông tin các proxy
    """
    results = []
    for port in Port.select():
        proxy_info = port.proxy_address
        results.append(f"socks5://{proxy_info}" if full_url else proxy_info)

    return PlainTextResponse('\n'.join(results))


router.add_api_websocket_route('', websocket_auto_update_endpoint(Port, PortOut, [SSH]))
