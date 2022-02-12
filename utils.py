import asyncio
import os.path
import socket

import psutil

import config


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
    timeout = config.get_config().getint('SSH', 'connection_timeout')
    with socket.socket() as s:
        s.settimeout(timeout)
        if s.connect_ex((host, port)):
            return False
    return True


async def wait_for_db_update(last_updated=0):
    """
    Wait until there is a database query that is not SELECT
    """
    while True:
        modified_time = os.path.getmtime('db.sqlite')
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
        return await completed.stdout.read()

    netstat = await run_shell_command("netstat -ano")
    pids = []

    # Get all process pids
    for line in netstat.splitlines():
        _, local_address, *_, pid = line.split()
        if local_address.endswith(f":{port_number}"):
            pids.append(int(pid))

    child_pids = [p.pid for p in psutil.Process().children(recursive=True)]

    if pids:
        # Kill the processes
        loop = asyncio.get_running_loop()
        for pid in pids:
            if pid in child_pids:
                await loop.run_in_executor(
                    None, lambda i: psutil.Process(i).kill(), pid
                )
        return True
    else:
        return False
