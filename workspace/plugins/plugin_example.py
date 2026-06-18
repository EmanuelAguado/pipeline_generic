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
        self._dict_previous_tasks = {
            "line": {"task": "sketch", "step": "ConceptArtStep"},
            "color": {"task": "line", "step": "ConceptArtStep"},
            "model": {"task": "modelblocking", "step": "ModelingStep"},
            "uvs": {"task": "model", "step": "ModelingStep"},
            "shading": {"task": "uvs", "step": "ModelingStep"},
            "fur": {"task": "shading", "step": "LookDevStep"},
            "blendShapes": {"task": "model", "step": "ModelingStep"},
            "rigging": {"task": "model", "step": "ModelingStep"},
            "animLib": {"task": "rigging", "step": "RiggingStep"},
            "blocking": {"task": "layout", "step": "LayoutStep"},
            "refine": {"task": "blocking", "step": "AnimationStep"},
            "fix": {"task": "refine", "step": "AnimationStep"},
            "bake": [{"task": "fix", "step": "AnimationStep"}, {"task": "refine", "step": "AnimationStep"}],
            "fxclean": {"task": "fxrough", "step": "FxStep"},
            "lighting": {"task": "prelight", "step": "LightingStep"},
        }
