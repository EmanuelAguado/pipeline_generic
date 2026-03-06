from logging import getLogger
from pathlib import Path
from gwaio.task_schema.plugins.maya_3d_plugin import Maya3DPlugin
from widgets.qt_classes.toolbar_example import ShellToolbar

logger = getLogger(__name__)


class DemoProjectPlugin(Maya3DPlugin):
    TITLE = "DemoProject"
    SG_PROJECT_ID = 551
    SHOTGRID_URL = "https://mondotv.shotgunstudio.com"
    PROJECT_UUID = "c5969a17-c0a1-44bc-88a2-cb3537e5d1d4"
    
    title = "Demo Project Generic"
    project_shortname = "dmp"
    env_name = "DEMOPROJECT"
    default_server_root = "C:/projects/plugin_example"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbars += [[ShellToolbar, "Shell Toolbar"]]
        self.WORKSPACE_PATH = Path(__file__).resolve().parents[1]
        self.CUSTOM_MAYA_TOOLS = Path(f"{self.WORKSPACE_PATH}/utilities/maya")
        self.CUSTOM_NUKE_TOOLS = Path(f"{self.WORKSPACE_PATH}/utilities/nuke")
