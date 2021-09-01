from typing import List

from fastapi.routing import APIRouter
from pony.orm import db_session

from models.ssh_models import SSH
from models.io_models import SSHIn, SSHOut

router = APIRouter()


@router.get('/')
def get_all_ssh():
    """
    Get all SSH from database.
    """
    with db_session:
        ssh_list = SSH.select()[:].to_list()
        return [SSHOut.from_orm(ssh) for ssh in ssh_list]


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
