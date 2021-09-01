import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass
from functools import wraps
from typing import cast

import aiohttp
from aiohttp_socks import ProxyConnector

import utils
from models import proxy_process


@dataclass
class ProxyInfo:
    port: int
    pid: int
    host: str = 'localhost'
    proxy_type: str = 'socks4'

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


def logging_wrapper(func):
    logger = logging.getLogger('Bitvise')
    logger.setLevel(logging.INFO)

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            result: ProxyInfo = func(*args, **kwargs)
            logger.info('|'.join(map(str, args)).ljust(50) + str(result.port))
            return result
        except BaseException as e:
            logger.info(
                '|'.join(map(str, args)).ljust(50) + e.__class__.__name__)
            raise

    return cast(func, wrapped)


@logging_wrapper
def connect_ssh_sync(host: str, username: str, password: str,
                     port: int = None) -> ProxyInfo:
    """
    Connect an SSH to specified port
    :param host:
    :param username:
    :param password:
    :param port: Local port to connect to
    :return: Proxy information if succeed. Will raise an error if failed
    """
    if not port:
        port = utils.get_free_port()
    process = subprocess.Popen([
        'executables/stnlc.exe', host,
        f'-user={username}', f'-pw={password}',
        '-proxyFwding=y', '-noRegistry', f'-proxyListPort={port}'
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.stdin.write(b'a\na\na')

    while not process.returncode:
        try:
            stdout, stderr = process.communicate(timeout=30)
        except TimeoutError:
            process.kill()
            process.communicate()
            raise ProxyConnectionError

        output = stdout.decode(errors='ignore').strip()
        if 'Enabled SOCKS/HTTP proxy forwarding on ' in output:
            port = re.search(
                r'Enabled SOCKS/HTTP proxy forwarding on .*?:(\d+)',
                output).group(1)
            proxy_info = ProxyInfo(port=int(port), pid=process.pid)
            if asyncio.run(get_proxy_ip(proxy_info.address)):
                return proxy_info
            else:
                process.kill()
                process.communicate()
                raise ProxyConnectionError
    raise ProxyConnectionError


async def connect_ssh(host: str, username: str, password: str,
                      port: int = None) -> ProxyInfo:
    """
    Connect an SSH to specified port
    :param host:
    :param username:
    :param password:
    :param port: Local port to connect to
    :return: Proxy information if succeed. Will raise an error if failed
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, connect_ssh_sync,
                                      host, username, password, port)


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
        proxy_process.kill_proxy_process(proxy_info.pid)
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
    except aiohttp.ClientError:
        return ''
