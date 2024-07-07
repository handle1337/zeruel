from util.logging_conf import logger
from models.proxy import Server

server_threads = []


def new_server(host='', port=7121):
    server = Server(host, port)
    server_threads.append(server)
    return server


def start(server, intercept=0):
    if intercept:
        server.intercepting = True
    server.start()


def stop(server_thread):
    logger.info(f"stopping server thread {server_thread}")
    if server_thread.running:
        server_thread.stop()
        server_thread.join()
        server_threads.remove(server_thread)


def stop_all():
    for server in server_threads:
        stop(server)


def get_threads():
    return server_threads
