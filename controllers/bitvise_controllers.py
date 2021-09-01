import asyncio
import logging
import subprocess
from dataclasses import dataclass

import aiohttp
import python_socks
from aiohttp_socks import ProxyConnector

import utils

logger = logging.getLogger('Bitvise')


@dataclass
class ProxyInfo:
    port: int
    pid: int
    host: str = 'localhost'
    proxy_type: str = 'socks5'

    @property
    def address(self):
        return f"{self.proxy_type}://{self.host}:{self.port}"


class BitviseError(Exception):
    """
    Base exception for all Bitvise and Proxy related errors.
    """


class ProxyConnectionError(BitviseError):
    """
    Cannot connect to specified SSH
    """


def connect_ssh_sync(host: str, username: str, password: str,
                     port: int = None, kill_after=False) -> ProxyInfo:
    if not port:
        port = utils.get_free_port()
    log_message = f"{host}|{username}|{password}|{port}"

    process = subprocess.Popen([
        'executables/stnlc.exe', host,
        f'-user={username}', f'-pw={password}',
        '-proxyFwding=y', '-noRegistry', f'-proxyListPort={port}'
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.stdin.write(b'a\na\na')
    process.stdin.flush()

    logger.info(f"{log_message} - SSH connection started.")
    while process.returncode is None:
        output = process.stdout.readline().decode(errors='ignore').strip()
        if 'Enabled SOCKS/HTTP proxy forwarding on ' in output:
            proxy_info = ProxyInfo(port=port, pid=process.pid)
            if asyncio.run(get_proxy_ip(proxy_info.address)):
                if kill_after:
                    process.kill()
                    process.communicate()
                logger.info(f"{log_message} - Connected successfully.")
                return proxy_info
            else:
                process.kill()
                process.communicate()
                logger.info(f"{log_message} - Cannot connect to proxy.")
                raise ProxyConnectionError

    logger.info(f"{log_message} - Bitvise quit with code {process.returncode}.")
    raise ProxyConnectionError


async def connect_ssh(host: str, username: str, password: str,
                      port: int = None, kill_after=False) -> ProxyInfo:
    """
    Connect an SSH to specified port
    :param host: SSH IP
    :param username: SSH username
    :param password: SSH password
    :param port: Local port to connect to
    :param kill_after: Set to True to kill the proxy process after verifying
    :return: Proxy information if succeed. Will raise an error if failed
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, connect_ssh_sync,
                                      host, username, password,
                                      port, kill_after)


async def verify_ssh(host: str, username: str, password: str) -> bool:
    """
    Verify if SSH is usable
    :param host:
    :param username:
    :param password:
    :return: True if SSH is connected successfully, returns False otherwise
    """
    try:
        await connect_ssh(host, username, password, kill_after=True)
        return True
    except ProxyConnectionError:
        return False


async def get_proxy_ip(proxy_address) -> str:
    """
    Retrieves proxy's real IP address. Returns empty string if failed
    :param proxy_address: Proxy connection address in <protocol>://<ip>:<port>
    :return: Proxy real IP address on success connection, empty string otherwise
    """
    try:
        connector = ProxyConnector.from_url(proxy_address)
        async with aiohttp.ClientSession(connector=connector) as client:
            async with client.get('https://api.ipify.org?format=text') as resp:
                return await resp.text()
    except (aiohttp.ClientError, python_socks.ProxyConnectionError,
            python_socks.ProxyError, python_socks.ProxyTimeoutError):
        return ''
