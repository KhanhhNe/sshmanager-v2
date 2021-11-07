import json
from typing import List

from fastapi.routing import APIRouter
from pony.orm import db_session, desc

from models.io_models import SSHIn, SSHOut
from models.ssh_models import SSH
from views import update_websocket

router = APIRouter()


@router.get('/')
def get_all_ssh():
    """
    Get all SSH from database.
    """
    with db_session:
        checked_ssh_list = SSH \
                               .select(lambda ssh: ssh.last_checked is not None) \
                               .order_by(desc(SSH.last_checked))[:] \
            .to_list()
        unchecked_ssh_list = SSH \
                                 .select(lambda ssh: ssh.last_checked is None)[
                             :] \
            .to_list()
        ssh_list = checked_ssh_list + unchecked_ssh_list
        return [SSHOut.from_orm(ssh) for ssh in ssh_list]


@router.websocket('/')
@update_websocket
def get_ssh_json():
    return [json.loads(s.json()) for s in get_all_ssh()]


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
