import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROCEDURES_PATH = (
    Path(__file__).resolve().parents[1] / "dept" / "layout" / "procedures.py"
)

MAYA_PROCEDURE_NAMES = [
    "import_file",
    "import_audio",
    "import_cam",
    "export_cam",
    "create_hierarchy_from_dict",
    "set_color_management",
    "import_image_plane",
    "reference_files",
    "reference_update",
    "return_reference_file_and_ns",
    "return_file",
    "run_playblast",
    "set_mh2_render",
    "set_time_config",
    "save_maya",
]


def _load_layout_procedures_module():
    cmds = Mock(name="cmds")
    maya_module = types.ModuleType("maya")
    maya_module.cmds = cmds

    class DummyMessageBox:
        Yes = 1
        No = 0
        question = Mock(return_value=Yes)

    qtwidgets_module = types.ModuleType("PySide6.QtWidgets")
    qtwidgets_module.QMessageBox = DummyMessageBox
    pyside_module = types.ModuleType("PySide6")
    pyside_module.QtWidgets = qtwidgets_module

    pipe_utils_module = types.ModuleType("pipe_utils")
    pipe_utils_module.return_highest_file = Mock(name="return_highest_file")

    resolver_module = types.ModuleType("resolver_utils")
    resolver_module.resolve = Mock(name="resolve", return_value="resolved_camera")

    maya_procedures_module = types.ModuleType("maya_procedures")
    procedure_mocks = {}
    for name in MAYA_PROCEDURE_NAMES:
        mock_fn = Mock(name=name)
        setattr(maya_procedures_module, name, mock_fn)
        procedure_mocks[name] = mock_fn

    def is_correct_task(*_task_names):
        def decorator(func):
            return func

        return decorator

    maya_procedures_module.is_correct_task = is_correct_task

    module_name = f"layout_procedures_under_test_{id(cmds)}"
    spec = importlib.util.spec_from_file_location(module_name, PROCEDURES_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {PROCEDURES_PATH}")

    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "maya": maya_module,
            "PySide6": pyside_module,
            "PySide6.QtWidgets": qtwidgets_module,
            "pipe_utils": pipe_utils_module,
            "resolver_utils": resolver_module,
            "maya_procedures": maya_procedures_module,
        },
        clear=False,
    ):
        spec.loader.exec_module(module)

    deps = {
        "cmds": cmds,
        "resolver": resolver_module.resolve,
        "message_box": DummyMessageBox,
        "return_highest_file": pipe_utils_module.return_highest_file,
    }
    deps.update(procedure_mocks)
    return module, deps


class TestLayoutProcedures(unittest.TestCase):
    def setUp(self):
        self.module, self.deps = _load_layout_procedures_module()

    @staticmethod
    def _make_gwaio(task_name="layout"):
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
                        "color_management": {"view_transform": "ACES"},
                    },
                    "playblast_config": {},
                    "playblast_viewport_config": {"display_appearance": "smoothShaded"},
                    "playblast_camera_config": {"overscan": 1.0},
                    "render_config": {"renderer": "vp2"},
                    "schema": {
                        "camera_name_schema": "{episode}_{sequence}_{shot}_cam",
                        "audio_name_schema": "{episode}_{sequence}_{shot}_audio",
                        "camera_file": "C:/server/production/publish/camera/cam.ma",
                        "asset_path_schema": (
                            "C:/server/production/publish/assets/"
                            "{asset_name}/{variant_name}/{task_name}"
                        ),
                    },
                    "hierarchy": {"root": "|world"},
                    "image_plane": None,
                }
            },
            _server_root="C:/server",
        )
        plugin.work_to_publish = Mock(
            return_value=(
                "ignored",
                "C:/server/production/publish/episodes/ep101/sq010/sh020/layout",
            )
        )
        plugin.async_find = Mock(return_value=[{"code": "char_main", "sg_asset_type": "ch"}])

        return SimpleNamespace(task=task, plugin=plugin)

    def test_lyt_preview_uses_layout_camera_and_runs_playblast(self):
        gwaio = self._make_gwaio(task_name="layout")
        self.deps["cmds"].file.return_value = (
            "C:/server/production/work/episodes/ep101/sq010/sh020/layout_scene_w003.ma"
        )

        self.module.lyt_preview_procedure(gwaio, resolution=[1280, 720])

        self.deps["run_playblast"].assert_called_once()
        kwargs = self.deps["run_playblast"].call_args.kwargs
        self.assertEqual(kwargs["camera"], "cam_master:cam_master")
        self.assertEqual(kwargs["resolution"], [1280, 720])
        self.assertEqual(
            gwaio.plugin.dccs["maya"]["playblast_config"]["filename"],
            "C:/server/production/work/episodes/ep101/sq010/sh020/layout_scene_w003",
        )
        self.deps["resolver"].assert_not_called()

    def test_lyt_preview_returns_if_camera_cannot_be_resolved(self):
        gwaio = self._make_gwaio(task_name="blocking")
        self.deps["cmds"].file.return_value = "C:/server/production/work/shot/anim_scene_w010.ma"
        self.deps["resolver"].return_value = ""

        self.module.lyt_preview_procedure(gwaio)

        self.deps["resolver"].assert_called_once()
        self.deps["run_playblast"].assert_not_called()

    def test_lyt_export_camera_procedure_calls_export_cam_with_expected_data(self):
        gwaio = self._make_gwaio(task_name="layout")
        gwaio.plugin.work_to_publish.return_value = ("ignored", "C:/publish/layout")
        self.deps["resolver"].return_value = "ep101_sq010_sh020_cam"

        self.module.lyt_export_camera_procedure(gwaio)

        self.deps["export_cam"].assert_called_once()
        kwargs = self.deps["export_cam"].call_args.kwargs
        self.assertEqual(
            kwargs["cam_input_name"], "|cam|cam_master:CAM_MASTER|cam_master:cam_master"
        )
        self.assertEqual(kwargs["cam_output_name"], "ep101_sq010_sh020_cam")
        self.assertEqual(kwargs["output_file"], Path("C:/publish/layout/dmp_camera.usd"))
        self.assertEqual(kwargs["cam_grp"], "bcam")

    def test_lyt_import_camera_procedure_imports_from_publish_path(self):
        gwaio = self._make_gwaio(task_name="layout")
        gwaio.plugin.work_to_publish.return_value = ("ignored", "C:/publish/layout")

        self.module.lyt_import_camera_procedure(gwaio)

        self.deps["import_cam"].assert_called_once_with(
            Path("C:/publish/layout/dmp_camera.usd")
        )

    def test_lyt_clean_camera_procedure_deletes_bcam_group(self):
        self.module.lyt_clean_camera_procedure(self._make_gwaio(task_name="layout"))
        self.deps["cmds"].delete.assert_called_once_with("|bcam")

    def test_lyt_creation_procedure_stops_if_user_rejects_overwrite(self):
        gwaio = self._make_gwaio(task_name="layout")
        self.deps["cmds"].file.return_value = "C:/server/production/work/shot/layout_002.ma"
        self.module.QMessageBox.question = Mock(return_value=self.module.QMessageBox.No)

        with patch.object(self.module.Path, "exists", return_value=True):
            self.module.lyt_creation_procedure(gwaio)

        self.module.QMessageBox.question.assert_called_once()
        self.deps["return_file"].assert_not_called()
        self.deps["save_maya"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
