import asyncio
import socket

from models.database import db


def get_ipv4_address():
    """
    Get this machine's local IPv4 address
    :return: IP address in LAN
    """
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def get_free_port():
    """
    Get a free port in local machine
    :return: Port number
    """
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]


async def wait_for_db_update():
    """
    Wait until there is a database query that is not SELECT
    """
    while True:
        if not db.last_sql.startswith('SELECT'):
            return
        await asyncio.sleep(1)
