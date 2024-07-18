from urllib.parse import urlparse
from util import logging_conf


def parse_data(data):
    if not data:
        return

    # TODO: parse origin/host as well
    # host : where the req is going
    # origin : where req is from

    print(f"Parsing: {data}")

    data_lines = data.decode('utf-8', errors='ignore').split('\n')

    print(f"Data lines: {data_lines}")

    host = ''
    method = data_lines[0].split(' ')[0]
    resource = data_lines[0].split(' ')[1]
    port = 80

    if resource[0] == '/':
        pass
    elif '://' in resource:
        parsed_url = urlparse(resource)
        host = parsed_url.netloc

        # TODO: There's some edge cases here we're not accounting for

        if ':' in host:
            split_host = host.split(':')
            host = split_host[0]
            port = int(split_host[1])

        if parsed_url.scheme == "http":
            port = 80
        elif parsed_url.scheme == "https":
            port = 443

    elif ':' in resource:
        split_host = resource.split(':')
        host = split_host[0]
        port = int(split_host[1])

    result = {"method": method, "host": host, "port": port, "data": data}

    logging_conf.logger.debug(f"\n\nPARSED DATA {result}\n\n")

    return result
