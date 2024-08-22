from views.repeater_view import RepeaterTab
from util import parser

repeater_tab = None
server_thread = None

def create_view(root):
    global repeater_tab
    repeater_tab = RepeaterTab(root=root)
    return repeater_tab

def update_request_widget(request):
    global repeater_tab
    repeater_tab.update_request_widget(request)

def set_server_thread(server):
    global server_thread
    server_thread = server

def send_request(request):
    request = parser.parse_data(request)
    print(request)
    server_thread.send_data()