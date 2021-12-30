import asyncio
import socket

import config
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


def can_connect_to_socket(host, port):
    """
    Try to connect to host:port using socket. Returns whether the connection
    succeed or not.
    :param host: Target host
    :param port: Target port
    :return: True if connected successfully. False otherwise.
    """
    conf = config.get_config()
    try:
        connection_timeout = conf.getint('SSH', 'connection_timeout')
        socket.create_connection((host, port), connection_timeout)
        return True
    except (ConnectionError, TimeoutError, socket.timeout):
        return False


async def wait_for_db_update():
    """
    Wait until there is a database query that is not SELECT
    """
    while True:
        if not db.last_sql.startswith('SELECT'):
            return
        await asyncio.sleep(1)
