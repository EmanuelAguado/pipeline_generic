import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    from maya import cmds  # type: ignore
except Exception:
    cmds = None


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PROCEDURES_PATH = WORKSPACE_ROOT / "dept" / "layout" / "procedures.py"
MAYA_SCRIPTS_PATH = WORKSPACE_ROOT / "utilities" / "maya" / "scripts"


def _prepend_to_path(path: Path):
    value = path.as_posix()
    if value not in sys.path:
        sys.path.insert(0, value)


def _install_missing_module_shims():
    try:
        import pipe_utils  # noqa: F401
    except ModuleNotFoundError:
        pipe_utils = types.ModuleType("pipe_utils")
        pipe_utils.return_highest_file = lambda *_args, **_kwargs: ""
        sys.modules["pipe_utils"] = pipe_utils

    try:
        import resolver_utils  # noqa: F401
    except ModuleNotFoundError:
        resolver_utils = types.ModuleType("resolver_utils")
        resolver_utils.resolve = lambda *_args, **_kwargs: ""
        sys.modules["resolver_utils"] = resolver_utils

    try:
        import maya_utils  # noqa: F401
    except ModuleNotFoundError:
        maya_utils = types.ModuleType("maya_utils")
        maya_utils.load_plugins = lambda *_args, **_kwargs: None
        sys.modules["maya_utils"] = maya_utils

    try:
        from PySide6.QtWidgets import QMessageBox  # noqa: F401
    except Exception:
        qtwidgets_module = types.ModuleType("PySide6.QtWidgets")

        class QMessageBox:
            Yes = 1
            No = 0

            @staticmethod
            def question(*_args, **_kwargs):
                return QMessageBox.Yes

        qtwidgets_module.QMessageBox = QMessageBox
        pyside_module = types.ModuleType("PySide6")
        pyside_module.QtWidgets = qtwidgets_module
        sys.modules["PySide6"] = pyside_module
        sys.modules["PySide6.QtWidgets"] = qtwidgets_module


def _load_layout_procedures():
    _prepend_to_path(MAYA_SCRIPTS_PATH)
    _install_missing_module_shims()
    module_name = "layout_procedures_maya_integration"
    spec = importlib.util.spec_from_file_location(module_name, LAYOUT_PROCEDURES_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {LAYOUT_PROCEDURES_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_gwaio(task_name="layout"):
    task = SimpleNamespace(
        name=task_name,
        cut_duration=48,
        server_path="C:/server/production/work/episodes/ep101/sq010/sh020/layout",
        assets="char_main",
    )
    task.serialize = Mock(return_value={"name": task_name})

    plugin = SimpleNamespace(
        schema={"version_regex": r"\d{3}"},
        attributes={
            "start_frame": 1001,
            "resolution": [1920, 1080],
        },
        dccs={
            "maya": {
                "attributes": {
                    "fps": 24,
                    "color_management": "sRGB",
                },
                "playblast_config": {},
                "playblast_viewport_config": {"polymeshes": True, "hos": True, "hud": True},
                "playblast_camera_config": {"overscan": 1.0},
                "render_config": {"multiSampleEnable": 1},
                "schema": {
                    "camera_name_schema": "{episode}_{sequence}_{shot}_cam",
                    "audio_name_schema": "{episode}_{sequence}_{shot}_audio",
                    "camera_file": "C:/server/production/publish/camera/cam.ma",
                    "asset_path_schema": (
                        "C:/server/production/publish/assets/"
                        "{asset_name}/{variant_name}/{task_name}"
                    ),
                },
                "hierarchy": {"|assets": ["*"]},
                "image_plane": None,
            }
        },
        _server_root="C:/server",
    )
    plugin.work_to_publish = Mock(return_value=("ignored", "C:/server/production/publish/layout"))
    plugin.async_find = Mock(return_value=[{"code": "char_main", "sg_asset_type": "ch"}])
    return SimpleNamespace(task=task, plugin=plugin)


@unittest.skipUnless(cmds is not None, "This test suite requires Maya.")
class TestLayoutProceduresMaya(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_layout_procedures()
        cls._tmp_dir_ctx = tempfile.TemporaryDirectory(prefix="layout_maya_tests_")
        cls.tmp_dir = Path(cls._tmp_dir_ctx.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir_ctx.cleanup()

    def setUp(self):
        cmds.file(new=True, force=True)

    def _save_scene(self, name: str) -> Path:
        scene_path = self.tmp_dir / f"{name}.ma"
        cmds.file(rename=scene_path.as_posix())
        cmds.file(save=True, type="mayaAscii", force=True)
        return scene_path

    def test_lyt_clean_camera_procedure_deletes_bcam_in_scene(self):
        cmds.createNode("transform", name="bcam")
        self.assertTrue(cmds.objExists("|bcam"))

        self.module.lyt_clean_camera_procedure(_build_gwaio(task_name="layout"))

        self.assertFalse(cmds.objExists("|bcam"))

    def test_lyt_preview_procedure_builds_playblast_from_current_scene(self):
        scene_path = self._save_scene("layout_preview_w003")
        gwaio = _build_gwaio(task_name="layout")

        with patch.object(self.module, "run_playblast", return_value="ok.mov") as run_playblast:
            self.module.lyt_preview_procedure(gwaio, resolution=[1280, 720])

        run_playblast.assert_called_once()
        kwargs = run_playblast.call_args.kwargs
        self.assertEqual(kwargs["camera"], "cam_master:cam_master")
        self.assertEqual(kwargs["resolution"], [1280, 720])
        self.assertEqual(
            gwaio.plugin.dccs["maya"]["playblast_config"]["filename"],
            scene_path.with_suffix("").as_posix(),
        )

    def test_lyt_creation_procedure_stops_when_overwrite_is_rejected(self):
        self._save_scene("layout_002")
        gwaio = _build_gwaio(task_name="layout")

        with patch.object(self.module.Path, "exists", return_value=True), patch.object(
            self.module.QMessageBox,
            "question",
            return_value=self.module.QMessageBox.No,
        ) as question, patch.object(self.module, "return_file") as return_file, patch.object(
            self.module, "save_maya"
        ) as save_maya:
            self.module.lyt_creation_procedure(gwaio)

        question.assert_called_once()
        return_file.assert_not_called()
        save_maya.assert_not_called()

    def test_lyt_export_camera_procedure_uses_publish_path(self):
        gwaio = _build_gwaio(task_name="layout")
        gwaio.plugin.work_to_publish.return_value = ("ignored", self.tmp_dir.as_posix())

        with patch.object(self.module.resolver_utils, "resolve", return_value="my_cam"), patch.object(
            self.module, "export_cam"
        ) as export_cam:
            self.module.lyt_export_camera_procedure(gwaio)

        export_cam.assert_called_once()
        kwargs = export_cam.call_args.kwargs
        self.assertEqual(kwargs["cam_output_name"], "my_cam")
        self.assertEqual(
            kwargs["output_file"],
            Path(self.tmp_dir.as_posix()) / "dmp_camera.usd",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)