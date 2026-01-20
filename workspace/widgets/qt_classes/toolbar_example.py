from gwaio.launcher.qtclasses.toolbar_base import BaseToolbar
from widgets.qt_classes.dock_example import DockShell

class ShellToolbar(BaseToolbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docks = [DockShell("Shell Editor")] 
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.shell_button = self.create_tool_button(
            self.env_handler.get_env("GWAIO_ICONS_PATH") + "/docs.png",
            "Open Shell Dock.")
        self.print_button = self.create_tool_button(
            self.env_handler.get_env("GWAIO_ICONS_PATH") + "/edit.png",
            "Open Shell Dock.")
        
    def create_layout(self):
        self.addWidget(self.shell_button)
        self.addWidget(self.print_button)

    def create_connections(self):
        print(self.docks)
        self.shell_button.clicked.connect(self.docks[0].show)
        self.print_button.clicked.connect(self.execute_print_command)

    def execute_print_command(self):
        print("Hello from Shell Toolbar!")

