from views.rootwindow_view import RootWindow
from views.bruteforce_view import BruteforceTab

from controllers import repeater
from controllers.intercept import InterceptController
from controllers.bruteforce import BruteforceController


class RootWindowController:
    def __init__(self, root, server):
        self.root_window = RootWindow(root)

        # Frames from RootWindow
        intercept_tab_frame = self.root_window.intercept_tab_frame
        repeater_tab_frame = self.root_window.repeater_tab_frame
        bruteforce_tab_frame = self.root_window.bruteforce_tab_frame

        # Intercept tab
        self.intercept_controller = InterceptController(root=intercept_tab_frame, server=server)

        # Repeater tab
        repeater.create_view(repeater_tab_frame)

        # Bruteforce tab
        self.bruteforce_controller = BruteforceController(root=bruteforce_tab_frame, intercept_controller=self.intercept_controller)


    def __del__(self):
        print("RootWindow Destroyed")
