import asyncio
import os.path
import re
import socket

import aiohttp
import asyncssh
import psutil
import python_socks
from aiohttp_socks import ProxyConnector


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


async def wait_for_db_update(last_updated=0):
    """
    Wait until there is a database query that is not SELECT
    """
    while True:
        modified_time = os.path.getmtime('data/db.sqlite')
        if last_updated < modified_time:
            return modified_time
        await asyncio.sleep(1)


async def kill_process_on_port(port_number: int):
    """
    Kill all child processes running on given port.

    :param port_number: Target port number
    :return: Whether any child process running on `port_number` is found
    """

    async def run_shell_command(command):
        completed = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE)
        return (await completed.stdout.read()).decode()

    netstat = await run_shell_command("netstat -ano")
    pids = []

    # Get all process pids
    for line in netstat.splitlines():
        try:
            _, local_address, *_, pid = line.split()
        except ValueError:
            continue
        if local_address.endswith(f":{port_number}"):
            pids.append(int(pid))

    child_pids = [p.pid for p in psutil.Process().children(recursive=True)]

    if pids:
        # Kill the processes
        loop = asyncio.get_running_loop()
        for pid in pids:
            if pid in child_pids:
                try:
                    await loop.run_in_executor(
                        None, lambda i: psutil.Process(i).kill(), pid
                    )
                except psutil.NoSuchProcess:
                    pass
        return True
    else:
        return False


def parse_ssh_file(file_content):
    """
    Parse SSH from file content. Expects IP, username, password, delimiting by
    some delimiter.

    :param file_content: Parsing file content
    :return: List of {ip: "...", username: "...", password: "..."}
    """
    results = []
    for line in file_content.splitlines():
        match = re.search(
            r'((?:[0-9]{1,3}\.){3}(?:[0-9]{1,3}))[;,|]([^;,|]*)[;,|]([^;,|]*)',
            line
        )
        if match:
            ip, username, password = match.groups()
            results.append({
                'ip': ip,
                'username': username,
                'password': password
            })
    return results


async def get_proxy_ip(proxy_address, tries=0) -> str:
    """
    Retrieves proxy's real IP address. Returns empty string if failed.

    :param proxy_address: Proxy connection address in <protocol>://<ip>:<port>
    :param tries: Total request tries
    :return: Proxy real IP address on success connection, empty string otherwise
    """
    try:
        connector = ProxyConnector.from_url(proxy_address)
        async with aiohttp.ClientSession(connector=connector) as client:
            # noinspection PyBroadException
            try:
                resp = await client.get('https://api.ipify.org?format=text')
                return await resp.text()
            except Exception:
                resp = await client.get('https://ip.seeip.org')
                return await resp.text()
    except (aiohttp.ClientError, python_socks.ProxyConnectionError, python_socks.ProxyError,
            python_socks.ProxyTimeoutError, ConnectionError, asyncio.exceptions.IncompleteReadError,
            asyncio.exceptions.TimeoutError):
        if not tries:
            return ''
        return await get_proxy_ip(proxy_address, tries=tries - 1)


async def kill_ssh_connection(connection: asyncssh.SSHClientConnection):
    """
    Kill the SSH connection.

    :param connection: SSH connection
    """
    await connection.__aexit__(None, None, None)
