from views.repeater_view import RepeaterTab

repeater_tab = None

def create_view(root):
    global repeater_tab
    repeater_tab = RepeaterTab(root=root)
    return repeater_tab

def update_request_widget(request):
    global repeater_tab
    repeater_tab.update_request_widget(request)