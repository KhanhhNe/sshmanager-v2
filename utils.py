import socket


def get_ipv4_address():
    """
    Get this machine's local IPv4 address
    :return: IP address in LAN
    """
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)
