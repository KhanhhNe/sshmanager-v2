from typing import List

from fastapi.routing import APIRouter

from models import ssh_models
from models.io_models import SSHIn, SSHOut

router = APIRouter()


@router.get('/')
def get_all_ssh():
    """
    Get all SSH from database.
    """
    ssh_list = ssh_models.get_all_ssh()
    return [SSHOut.from_orm(ssh) for ssh in ssh_list]


@router.post('/')
def add_ssh(ssh_list: List[SSHIn]):
    """
    Add a list of SSH into the database. The list will be checked automatically
    when a runner got to it.
    """
    ssh_models.add_ssh(ssh_list)
    return {}


@router.delete('/')
def delete_ssh(ssh_list: List[SSHIn]):
    """
    Remove a list of SSH from the database.
    """
    ssh_models.remove_ssh(ssh_list)
    return {}
