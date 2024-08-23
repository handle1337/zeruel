import enum
import socket
import ssl

from util import parser
from util.enums import Protocols


def get_port_upgrade(host, port=80):
    protocol = probe_tls_support(host, port)
    if port != 80:
        return port, protocol
    else:
        # check if port 443 is https, upgrade if so
        protocol = probe_tls_support(host, port=443)
        if protocol == Protocols.HTTPS:
            port = 443
    return port, protocol

def get_remote_socket_from_request(parsed_data):
    host = parsed_data["host"]
    parsed_protocol = parsed_data["protocol"]
    if parsed_data["port"]:
        port = parsed_data["port"]
    elif parsed_protocol:
        port = parsed_protocol
    else:
        port = 80
    try:
        port, protocol = get_port_upgrade(host, port)
        remote_socket = socket.create_connection((host, port))
        if protocol == Protocols.HTTPS:
             return wrap_remote_socket(remote_socket, host)
        return remote_socket

    except Exception as e:
        print(e)
        return



def wrap_client_socket(client_socket, cert_path, key_path):
    client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    client_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    client_ssl_socket = client_ctx.wrap_socket(sock=client_socket, server_side=True)
    return client_ssl_socket


def wrap_remote_socket(remote_socket, hostname):
    remote_ctx = ssl.create_default_context()
    remote_ssl_socket = remote_ctx.wrap_socket(remote_socket, server_hostname=hostname)
    return remote_ssl_socket


def probe_tls_support(hostname, port=443) -> enum.Enum:
    """

    :param hostname: Remote target hostname
    :param port: Remote target port, default is 443
    :return: Protocol enum
    """

    remote_socket = socket.create_connection((hostname, port))
    try:
        remote_ssl_socket = wrap_remote_socket(remote_socket, hostname)
        print(f"Version {remote_ssl_socket.version()} host: {hostname}")
        return Protocols.HTTPS
    except socket.error:
        return Protocols.HTTP

def send_request(request: bytes):
    response = b''
    parsed_request = parser.parse_data(request)
    print(parsed_request)
    remote_socket = get_remote_socket_from_request(parsed_request)
    try:
        remote_socket.sendall(parsed_request["data"])
        while True:
            chunk = remote_socket.recv(4096)
            if not chunk:
                break
            response = response + chunk
        print(response)
        return response

    except Exception as e:
        print(f"Error sending request: {e}")