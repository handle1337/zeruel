from urllib.parse import urlparse
from util.enums import Protocols
from util.logging_conf import logger

def parse_request_body(body):
    body = ''
    return body

def parse_request_headers(request):
    headers = []

    decoded_request = request.decode('utf-8', errors='ignore')
    split_lines = decoded_request.split('\r\n')
    split_lines.pop(0)
    split_lines = list(filter(None, split_lines))
   # print(f"split filtered lines{split_lines}")

    for line in split_lines:
        header = line.split(': ')
        if len(header) == 2:
            headers.append(tuple(header))

    headers = dict(headers)
    return headers


def parse_url(url: str) -> tuple:
    host, port, protocol = None, None, None

    if '://' in url:
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        if ':' in host:
            split_host = host.split(':')
            host = split_host[0]
            port = int(split_host[1])

        if parsed_url.scheme == "http":
            protocol = Protocols.HTTP
        elif parsed_url.scheme == "https":
            protocol = Protocols.HTTPS

    elif ':' in url:
        split_host = url.split(':')
        host = split_host[0]
        port = int(split_host[1])
    else:
        host = url

    return host, port, protocol


def parse_data(data: bytes) -> dict:
    if not data:
        return {}
    # None by default, if port is found in request we use that in other functions on a case-to-case basis
    port = None

    data_lines = data.decode('utf-8', errors='ignore').split('\r\n')
    print(f"data lines: {data_lines}")
    method = data_lines[0].split(' ')[0]
    resource = data_lines[0].split(' ')[1]
    headers = parse_request_headers(data)
    body = data_lines[-1]


    """
    Check if request for a resource or host ex:
    GET /api/users
    or 
    GET eu.httpbin.com:80
    """
    if resource[0] == '/':
        host = headers['Host']
    else:
        host = resource

    # TODO: There is possible edge-cases where ":" might be used for more than just indicating ports in url/resource

    parsed_host = parse_url(host)
    protocol = parsed_host[2]

    if parsed_host[1]:
        port = int(parse_url(host)[1])

    host = parsed_host[0]

    result = {"method": method,
              "host": host,
              "port": port,
              "data": data,
              "headers": headers,
              "protocol": protocol,
              "body": body}
    print(f"result {method} {host} {port} {headers}")
    return result
