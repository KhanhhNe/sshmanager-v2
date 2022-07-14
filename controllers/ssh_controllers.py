import logging
from dataclasses import dataclass
from typing import List

import asyncssh
import asyncssh.compression
import asyncssh.encryption
import asyncssh.kex
import asyncssh.mac
import trio

import utils
from utils import get_proxy_ip

logger = logging.getLogger('Ssh')


def get_algs_config():
    config = dict(server_host_key_algs=[b'ssh-rsa'],  # Old dropbear servers compatibility
                  kex_algs=asyncssh.kex.get_kex_algs(),
                  encryption_algs=asyncssh.encryption.get_encryption_algs(),
                  mac_algs=asyncssh.mac.get_mac_algs(),
                  compression_algs=asyncssh.compression.get_compression_algs(),
                  signature_algs=(asyncssh.public_key.get_x509_certificate_algs() +
                                  asyncssh.public_key.get_public_key_algs()))

    # OpenSSH 7.2 compatibility
    if b'ecdh-sha2-nistp521' in config['kex_algs']:
        config['kex_algs'].remove(b'ecdh-sha2-nistp521')

    for key, algs in config.items():
        config[key] = [alg.decode() for alg in algs]

    return config


@dataclass
class ProxyInfo:
    port: int
    connection: asyncssh.SSHClientConnection
    host: str = 'localhost'
    proxy_type: str = 'socks5'

    @property
    def address(self):
        return f"{self.proxy_type}://{self.host}:{self.port}"


proxies: List[ProxyInfo] = []


class SSHError(Exception):
    """
    Exception for SSH-related issues.
    """


async def connect_ssh(host: str, username: str, password: str, port: int = None):
    """
    Connect to the SSH and returning the Socks5 proxy information.

    :param host: SSH host
    :param username: SSH username
    :param password: SSH password
    :param port: Local port to forward to
    :return: ProxyInfo object containing the forwarded Socks5 proxy
    """
    if not port:
        port = utils.get_free_port()

    try:
        await kill_proxy_on_port(port)
    except SSHError:
        pass

    start_time = trio.current_time()
    ssh_info = f"{host:15} | {port:5}"

    def run_time():
        return '{:4.1f}'.format(trio.current_time() - start_time)

    try:
        try:
            connection = await asyncssh.connect(
                host, username=username, password=password,
                known_hosts=None, **get_algs_config()
            )

            await connection.forward_socks('', port)
            proxy_info = ProxyInfo(port=port, connection=connection)

            if not await get_proxy_ip(proxy_info.address):
                await utils.kill_ssh_connection(connection)
                raise SSHError("Cannot connect to forwarded proxy.")
        except (OSError, asyncssh.Error) as exc:
            raise SSHError(f"{type(exc).__name__}: {exc}.")

    except SSHError as exc:
        logger.debug(f"{ssh_info} ({run_time()}s) - {exc}")
        raise

    else:
        logger.debug(f"{ssh_info} ({run_time()}s) - Connected successfully.")

    proxies.append(proxy_info)
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


async def kill_proxy_on_port(port: int):
    """
    Kill proxy on specified port number.

    :param port: Target port number
    """
    for proxy in proxies:
        if proxy.port == port:
            proxies.remove(proxy)
            await utils.kill_ssh_connection(proxy.connection)
            break
    else:
        raise SSHError(f"No proxy on port {port} found.")
