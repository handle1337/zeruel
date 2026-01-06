import logging
from models.proxy import Server

logger = logging.getLogger(__name__)

server_threads = []


def new_server(host='', port=7121):
    server = Server(host, port)
    server_threads.append(server)
    return server


def start(server_thread, intercept=0):
    logger.info(f"Starting server thread {server_thread}")
    if intercept:
        server_thread.intercepting = True
    server_thread.start()


def stop(server_thread):
    logger.info(f"Stopping server thread {server_thread}")
    if server_thread.running:
        server_thread.stop()
        server_thread.join()
        server_threads.remove(server_thread)


def stop_all():
    for server in server_threads:
        stop(server)
    logger.warning(f"Stopped all server threads")


def get_threads():
    return server_threads
