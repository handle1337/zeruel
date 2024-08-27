from views.rootwindow_view import RootWindow

from controllers.intercept import InterceptController



class RootWindowController:
    def __init__(self, root, server):
        self.root_window = RootWindow(root)

        intercept_tab_frame = self.root_window.intercept_tab_frame

        self.intercept_controller = InterceptController(root=intercept_tab_frame, server=server)

        #self.intercept_tab = InterceptTab(self.RootWindow.repeater_tab, None)

    def __del__(self):
        print("RootWindow Destroyed")
