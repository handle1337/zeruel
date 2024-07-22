from urllib.parse import urlparse
from util.logging_conf import logger


def parse_request_headers(request):
    decoded_request = request.decode('utf-8', errors='ignore')
    split_lines = decoded_request.split('\r\n')
    split_lines.pop(0)
    split_lines = list(filter(None, split_lines))
    headers = dict(s.split(': ') for s in split_lines)
    return headers


def parse_url(url: str) -> tuple:
    host, port = None, None

    if '://' in url:
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        if ':' in host:
            split_host = host.split(':')
            host = split_host[0]
            port = int(split_host[1])

        if parsed_url.scheme == "http":
            port = 80
        elif parsed_url.scheme == "https":
            port = 443

    elif ':' in url:
        split_host = url.split(':')
        host = split_host[0]
        port = int(split_host[1])

    return host, port


def parse_data(data):
    if not data:
        return
    # atm We try 80 by default, we probe for https in proxy, then we change to that later
    # during proxy operations
    port = 80

    data_lines = data.decode('utf-8', errors='ignore').split('\r\n')
    print(data_lines)
    method = data_lines[0].split(' ')[0]
    resource = data_lines[0].split(' ')[1]
    headers = parse_request_headers(data)

    if resource[0] == '/':
        host = headers['Host']
        print(host)
        #port = int(parse_url(host)[1])
    else:
        host = parse_url(resource)[0]
        #port = int(parse_url(resource)[1])

    result = {"method": method, "host": host, "port": port, "data": data, "headers": headers}
    print(f"{method} {host} {port} {headers}")
    return result
