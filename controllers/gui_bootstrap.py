from views.rootwindow_view import RootWindow

from controllers import repeater
from controllers.intercept import InterceptController


class RootWindowController:
    def __init__(self, root, server):
        self.root_window = RootWindow(root)

        intercept_tab_frame = self.root_window.intercept_tab_frame
        repeater_tab_frame = self.root_window.repeater_tab_frame

        self.intercept_controller = InterceptController(root=intercept_tab_frame, server=server)

        repeater.create_view(repeater_tab_frame)




    def __del__(self):
        print("RootWindow Destroyed")
