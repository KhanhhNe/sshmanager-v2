import json
import logging
import os.path
import socket

import aiohttp
import asyncssh
import pyparsing as pp
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


def parse_ssh_file(file_content):
    """
    Parse SSH from file content. Expects IP, username, password, delimiting by
    some delimiter.

    :param file_content: Parsing file content
    :return: List of {ip: "...", username: "...", password: "..."}
    """
    results = []

    sep = pp.Char(';,|').suppress()
    ip = pp.common.ipv4_address
    port = pp.Word(pp.nums, max=5)
    user_pass = pp.Word(pp.printables, exclude_chars=';,|')

    ssh_parser = (pp.SkipTo(ip) +
                  ip('ip') + sep +
                  pp.Opt(port('ssh_port') + sep) +
                  user_pass('username') + sep +
                  user_pass('password'))

    for line in file_content.splitlines():
        try:
            results.append(ssh_parser.parse_string(line).as_dict())
        except pp.ParseException:
            continue

    return results


async def get_proxy_ip(proxy_address, tries=1) -> str:
    """
    Retrieves proxy's real IP address. Returns empty string if failed.

    :param proxy_address: Proxy connection address in <protocol>://<ip>:<port>
    :param tries: Total request tries
    :return: Proxy real IP address on success connection, empty string otherwise
    """
    connector = ProxyConnector.from_url(proxy_address, enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector) as client:
        for retry in range(tries):
            # noinspection PyBroadException
            try:
                # noinspection PyBroadException
                try:
                    resp = await client.get('https://api.ipify.org?format=text')
                    return await resp.text()
                except Exception:
                    resp = await client.get('https://ip.seeip.org')
                    return await resp.text()
            except Exception:
                pass

    return ''


async def kill_ssh_connection(connection: asyncssh.SSHClientConnection):
    """
    Kill the SSH connection.

    :param connection: SSH connection
    """
    await connection.__aexit__(None, None, None)


def configure_logging():
    """
    Configure console logging and file logging.
    """

    def logging_filter(record: logging.LogRecord):
        if any([
            record.exc_info and record.exc_info[0] in [BrokenPipeError],
            record.name == 'Ssh'
        ]):
            return False
        return True

    # Console logging handler
    console_logging = logging.StreamHandler()
    console_logging.setLevel(logging.INFO
                             if not os.environ.get('DEBUG')
                             else logging.DEBUG)
    console_logging.addFilter(logging_filter)

    # File logging handler
    file_logging = logging.FileHandler('data/debug.log', mode='w')
    file_logging.setLevel(logging.DEBUG)
    file_logging.addFilter(logging_filter)

    # SSH debug logging handler
    ssh_logging = logging.FileHandler('data/ssh-debug.log', mode='w')
    ssh_logging.setLevel(logging.DEBUG)
    ssh_logging.addFilter(lambda rec: rec.name == 'Ssh')

    # Config the logging module
    log_config = json.load(open('logging_config.json'))
    formatter_config = log_config['formatters']['standard']
    logging.basicConfig(level=logging.DEBUG,
                        format=formatter_config['format'],
                        datefmt=formatter_config['datefmt'],
                        handlers=[file_logging, console_logging, ssh_logging],
                        force=True)

    for logger in ['multipart.multipart', 'charset_normalizer', 'asyncio']:
        logging.getLogger(logger).setLevel(logging.WARNING)
