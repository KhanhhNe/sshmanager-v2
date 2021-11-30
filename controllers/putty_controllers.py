import asyncio
import logging
import subprocess
import time
from dataclasses import dataclass

import aiohttp
import python_socks
from aiohttp_socks import ProxyConnector

import utils

logger = logging.getLogger('Putty')


@dataclass
class ProxyInfo:
    port: int
    pid: int
    host: str = 'localhost'
    proxy_type: str = 'socks5'

    @property
    def address(self):
        return f"{self.proxy_type}://{self.host}:{self.port}"


class PuttyError(Exception):
    """
    Base exception for all Putty and Proxy related errors.
    """


class ProxyConnectionError(PuttyError):
    """
    Cannot connect to specified SSH
    """


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
    if not port:
        port = utils.get_free_port()
    log_message = f"{host}|{username}|{password}|{port}"
    start_time = time.perf_counter()

    def run_time():
        return round(time.perf_counter() - start_time, 1)

    loop = asyncio.get_event_loop()
    if not await loop.run_in_executor(None,
                                      utils.can_connect_to_socket,
                                      host, 21):
        logger.debug(
            f"{log_message} ({run_time()}s) - Connection to SSH failed.")
        raise ProxyConnectionError

    process = await asyncio.create_subprocess_exec(
        'executables/PLINK.EXE', f'{username}@{host}', '-pw', password,
        '-D', f'0.0.0.0:{port}',
        '-v',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    process.stdin.write(b'y\ny\ny\n')

    while process.returncode is None:
        output = (await process.stdout.readline()) \
            .decode(errors='ignore').strip()
        if 'SOCKS dynamic forwarding' in output:
            proxy_info = ProxyInfo(host=utils.get_ipv4_address(),
                                   port=port, pid=process.pid)
            if await get_proxy_ip(proxy_info.address):
                if kill_after:
                    process.kill()
                logger.debug(
                    f"{log_message} ({run_time()}s) - Connected successfully.")
                return proxy_info
            else:
                logger.debug(
                    f"{log_message} ({run_time()}s) - Cannot connect to proxy.")
                raise ProxyConnectionError
        elif 'Password authentication failed' in output or \
                'FATAL ERROR' in output:
            logger.debug(
                f"{log_message} ({run_time()}s) - {output}")
            raise ProxyConnectionError

    process.kill()
    logger.debug(
        f"{log_message} ({run_time()}s) - Exit code {process.returncode}.")
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
        await connect_ssh(host, username, password, kill_after=True)
        return True
    except ProxyConnectionError:
        return False


async def get_proxy_ip(proxy_address, tries=0) -> str:
    """
    Retrieves proxy's real IP address. Returns empty string if failed
    :param proxy_address: Proxy connection address in <protocol>://<ip>:<port>
    :param tries: Total request tries
    :return: Proxy real IP address on success connection, empty string otherwise
    """
    try:
        connector = ProxyConnector.from_url(proxy_address)
        async with aiohttp.ClientSession(connector=connector) as client:
            try:
                async with client.get(
                        'https://api.ipify.org?format=text') as resp:
                    return await resp.text()
            except:
                async with client.get('https://ip.seeip.org') as resp:
                    return await resp.text()
    except (aiohttp.ClientError, python_socks.ProxyConnectionError,
            python_socks.ProxyError, python_socks.ProxyTimeoutError,
            ConnectionError, asyncio.exceptions.IncompleteReadError,
            asyncio.exceptions.TimeoutError):
        if not tries:
            return ''
        return await get_proxy_ip(proxy_address, tries=tries - 1)
