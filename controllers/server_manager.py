from models.proxy import Server

server_threads = []


def new_server(host='', port=7121):
    server = Server(host, port)
    return server


def start(server, intercept=0):
    if intercept:
        server.intercepting = True
    server.start()
    server_threads.append(server)


def stop(server_thread):
    if server_thread.running:
        server_thread.stop()
        server_thread.join()
        server_threads.remove(server_thread)


def get_threads(self):
    return server_threads
