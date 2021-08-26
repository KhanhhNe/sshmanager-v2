import asyncio
import logging
import re
import socket
from dataclasses import dataclass
from functools import wraps
from typing import cast

import aiohttp
from aiosocks.connector import ProxyClientRequest, ProxyConnector

from backend_src import models


@dataclass
class ProxyInfo:
    port: int
    pid: int
    host: str = 'localhost'
    proxy_type: str = 'socks4'

    @property
    def address(self):
        return f"{self.proxy_type}://{self.host}:{self.port}"


class BitviseError(BaseException):
    """
    Base exception for all Bitvise and Proxy related errors.
    """


class ProxyConnectionError(BitviseError):
    """
    Cannot connect to specified SSH
    """


def logging_wrapper(func):
    logger = logging.getLogger('Bivise')
    logger.setLevel(logging.INFO)

    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            result: ProxyInfo = await func(*args, **kwargs)
            logger.info('|'.join(map(str, args)).ljust(50) + str(result.port))
            return result
        except BaseException as e:
            logger.info('|'.join(map(str, args)).ljust(50) + e.__class__.__name__)
            raise

    return cast(func, wrapped)


@logging_wrapper
async def connect_ssh(host: str, username: str, password: str, port: int = None) -> ProxyInfo:
    """
    Connect an SSH to specified port
    :param host:
    :param username:
    :param password:
    :param port: Local port to connect to
    :return: Proxy information if succeed. Will raise an error if something went wrong
    """
    process = await asyncio.create_subprocess_exec('executables/stnlc.exe', host,
                                                   f'-user={username}', f'-pw={password}',
                                                   '-proxyFwding=y', '-noRegistry',
                                                   f'-proxyListPort={str(port or _get_free_port())}',
                                                   stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    models.add_proxy_process(process.pid)
    process.stdin.write(b'a\na\na')

    while not process.returncode:
        done, pending = await asyncio.wait({asyncio.create_task(process.stdout.readline())}, timeout=30)
        # Kill process if timed out
        if pending:
            models.kill_proxy_process(process.pid)
            raise ProxyConnectionError

        output = done.pop().result().decode(errors='ignore').strip()
        if 'Enabled SOCKS/HTTP proxy forwarding on ' in output:
            port = re.search(r'Enabled SOCKS/HTTP proxy forwarding on .*?:(\d+)', output).group(1)
            proxy_info = ProxyInfo(port=int(port), pid=process.pid)
            if await get_proxy_ip(proxy_info.address):
                return proxy_info
            else:
                models.kill_proxy_process(process.pid)
                raise ProxyConnectionError
    raise ProxyConnectionError


async def verify_ssh(host: str, username: str, password: str) -> bool:
    """
    Verify if SSH is usable
    :param host:
    :param username:
    :param password:
    :return: True if SSH is connected successfully, returns False otherwise
    """
    try:
        proxy_info = await connect_ssh(host, username, password)
        models.kill_proxy_process(proxy_info.pid)
        return True
    except ProxyConnectionError:
        return False


async def get_proxy_ip(proxy_address) -> str:
    """
    Retrieves proxy's real IP address. Returns empty string on connection failure
    :param proxy_address: Proxy connection address, in format <protocol>://<ip>:<port>
    :return: Proxy real IP address on success connection, empty string otherwise
    """
    try:
        async with aiohttp.ClientSession(connector=ProxyConnector(remote_resolve=False),
                                         request_class=ProxyClientRequest) as client:
            async with client.get('https://api.ipify.org?format=text', proxy=proxy_address) as resp:
                return await resp.text()
    except aiohttp.ClientError:
        return ''


def _get_free_port():
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]
