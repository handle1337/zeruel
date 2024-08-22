import enum
import socket
import ssl


class Protocols(enum.Enum):
    HTTP = enum.auto()
    HTTPS = enum.auto()


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