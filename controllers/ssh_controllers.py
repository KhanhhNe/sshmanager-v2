import logging
import time
from dataclasses import dataclass

import asyncssh

import utils
from utils import get_proxy_ip

logger = logging.getLogger('Ssh')


@dataclass
class ProxyInfo:
    port: int
    connection: asyncssh.SSHClientConnection
    host: str = 'localhost'
    proxy_type: str = 'socks5'

    @property
    def address(self):
        return f"{self.proxy_type}://{self.host}:{self.port}"


class SSHError(Exception):
    """
    Exception for SSH-related issues.
    """


async def connect_ssh(host: str, username: str, password: str, port: int = None):
    """
    Connect to the SSH and returning the Socks5 proxy information.

    :param host: SSH host
    :param username: SSH username
    :param password: SSH possword
    :param port: Local port to forward to
    :return: ProxyInfo object containing the forwarded Socks5 proxy
    """
    if not port:
        port = utils.get_free_port()

    start_time = time.perf_counter()
    ssh_info = f"{host:15} | {port:5}"

    try:
        try:
            connection = await asyncssh.connect(host, username=username, password=password,
                                                known_hosts=None)
            await connection.forward_socks('', port)
            proxy_info = ProxyInfo(port=port, connection=connection)

            if not await get_proxy_ip(proxy_info.address):
                await utils.kill_ssh_connection(connection)
                raise SSHError("Cannot connect to forwarded proxy.")
        except (OSError, asyncssh.Error) as exc:
            raise SSHError(f"{exc}.")

    except SSHError as exc:
        run_time = '{:4.1f}'.format(time.perf_counter() - start_time)
        logger.debug(f"{ssh_info} ({run_time}s) - {exc}")
        raise

    else:
        run_time = '{:4.1f}'.format(time.perf_counter() - start_time)
        logger.debug(f"{ssh_info} ({run_time}s) - Connected successfully.")

    return proxy_info


async def verify_ssh(host: str, username: str, password: str) -> bool:
    """
    Verify if SSH is usable.

    :param host:
    :param username:
    :param password:
    :return: True if SSH is connected successfully, returns False otherwise
    """
    try:
        proxy_info = await connect_ssh(host, username, password)
        await utils.kill_ssh_connection(proxy_info.connection)
        return True
    except SSHError:
        return False
