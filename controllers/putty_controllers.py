import asyncio
import logging
import subprocess
import time
from dataclasses import dataclass

import utils
from utils import get_proxy_ip

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
    Cannot connect to specified SSH.
    """


async def connect_ssh(host: str, username: str, password: str, port: int = None,
                      kill_after=False) -> ProxyInfo:
    """
    Connect an SSH to specified port.

    :param host: SSH IP
    :param username: SSH username
    :param password: SSH password
    :param port: Local port to connect to
    :param kill_after: Set to True to kill the proxy process after verifying
    :return: Proxy information if succeed. Will raise an error if failed
    """
    if not port:
        port = utils.get_free_port()
    start_time = time.perf_counter()

    def log(msg):
        log_message = f"{host:15} | {port:5}"
        run_time = '{:4.1f}'.format(time.perf_counter() - start_time)
        logger.debug(f"{log_message} ({run_time}s) - {msg}")

    def kill(p):
        try:
            p.kill()
        except ProcessLookupError:
            pass

    process = await asyncio.create_subprocess_exec(
        'PLINK.EXE', f'{username}@{host}', '-pw', password,
        '-D', f'0.0.0.0:{port}',
        '-v',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    process.stdin.write(b'y\n' * 50)

    while process.returncode is None:
        output = (await process.stdout.readline()).decode(errors='ignore').strip()
        if 'SOCKS dynamic forwarding' in output:
            proxy_info = ProxyInfo(host=utils.get_ipv4_address(), port=port, pid=process.pid)
            if await get_proxy_ip(proxy_info.address):
                if kill_after:
                    kill(process)
                log(f"Connected successfully.")
                return proxy_info
            else:
                kill(process)
                log(f"Cannot connect to proxy.")
                raise ProxyConnectionError
        elif (
                'Password authentication failed' in output or
                'FATAL ERROR' in output or
                'Access denied' in output
        ):
            kill(process)
            log(f"{output}")
            raise ProxyConnectionError

    log(f"Exit code {process.returncode}.")
    raise ProxyConnectionError


async def verify_ssh(host: str, username: str, password: str) -> bool:
    """
    Verify if SSH is usable.

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
