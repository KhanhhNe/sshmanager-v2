from datetime import datetime, timedelta
from typing import List

from fastapi import UploadFile
from fastapi.routing import APIRouter
from pony.orm import ObjectNotFound, db_session

from controllers import actions
from models import Port, SSH
from models.io_models import SSHIn, SSHOut
from views.websockets import websocket_auto_update_endpoint

router = APIRouter()


@router.get('', response_model=List[SSHOut])
def get_all_ssh():
    """
    Lấy thông tin toàn bộ SSH.

    :return: Danh sách thông tin SSH
    """
    with db_session(optimistic=False):
        ssh_list = SSH.select().prefetch(Port)[:].to_list()
    return [SSHOut.from_orm(ssh) for ssh in ssh_list]


@router.post('', response_model=List[SSHOut])
@db_session
def add_ssh(ssh_list: List[SSHIn]):
    """
    Tạo SSH.

    :param ssh_list: Danh sách thông tin SSH muốn

    :return: Thông tin SSH sau khi tạo
    """
    results = []
    for ssh in ssh_list:
        if not SSH.exists(**ssh.dict()):
            s = SSH(**ssh.dict())
            results.append(s)

    return [SSHOut.from_orm(s) for s in results]


@router.delete('', response_model=int)
@db_session
def delete_ssh(ssh_ids: List[int]):
    """
    Xoá SSH.

    :param ssh_ids: ID của các SSH muốn xoá

    :return: Số lượng SSH đã xoá
    """
    deleted = 0

    for ssh_id in ssh_ids:
        try:
            ssh = SSH[ssh_id]
            ssh.delete()
            deleted += 1
        except ObjectNotFound:
            continue

    return deleted


@router.post('/upload', response_model=List[SSHOut])
async def upload_ssh(ssh_file: UploadFile):
    """
    Tải lên file chứa thông tin SSH (file từ các dịch vụ SSH).

    :param ssh_file: File chứa thông tin SSH

    :return: Thông tin SSH sau khi tạo
    """
    file_content = (await ssh_file.read()).decode()
    ssh_ids = await asyncio.to_thread(actions.insert_ssh_from_file_content, file_content)
    with db_session(optimistic=False):
        # Re-query SSHs and format into output model
        return [SSHOut.from_orm(SSH[ssh_id]) for ssh_id in ssh_ids]


@router.get('/check-speed')
def get_ssh_checking_speed():
    """
    Lấy thông tin tốc độ kiểm tra SSH.
    """
    with db_session(optimistic=False):
        total_minutes = 2
        total_ssh_checked = SSH.select(
            lambda s: s.last_checked >= datetime.now() - timedelta(minutes=total_minutes)
        ).count()
        return total_ssh_checked / total_minutes


router.add_api_websocket_route('', websocket_auto_update_endpoint(SSH, SSHOut, [Port]))
