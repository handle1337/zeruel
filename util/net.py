import enum
import errno
import socket
import ssl
import time
from textwrap import indent

from requests import Request, Session
from controllers import queue_manager
from util import parser, enums
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
        print(f"get remote socket {(host, port)}")
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
    # TODO: check content encoding in req headers, decode/unzip content
    #https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding?utm_source=mozilla&utm_medium=devtools-netmonitor&utm_campaign=default

    response = b''
    parsed_request = parser.parse_data(request)
    print(parsed_request)
    remote_socket = get_remote_socket_from_request(parsed_request)
    remote_socket.settimeout(2)

    remote_socket.sendall(parsed_request["data"])


    while True:
        try:
            chunk = remote_socket.recv(4096)
        except socket.timeout:
            break
        except socket.error as e:
            print(f"Socker error: {e}")
            break
        else:
            if chunk:
                response = response + chunk
            else:
                break

    queue_manager.server_response_queue.put(response.decode(errors='ignore'))
    queue_manager.server_response_queue.put(enums.EOR) #end of req

