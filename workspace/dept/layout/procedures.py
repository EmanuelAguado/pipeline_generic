from logging import getLogger
from pathlib import Path
from re import compile, sub
from typing import TYPE_CHECKING, List
from os import fspath

from PySide6.QtWidgets import QMessageBox  # type: ignore
from maya import cmds  # type: ignore

from pipe_utils import return_highest_file  # type: ignore
from maya_procedures import (  # type: ignore
    import_file,
    import_audio,
    import_camera,
    create_hierarchy_from_dict,
    set_color_management,
    set_hud,
    import_image_plane,
    reference_files,
    return_file,
    run_playblast,
    set_mh2_render,
    set_time_config,
    save_maya,
)

if TYPE_CHECKING:
    import gwaio

VERSION_REGEX = compile("(?<=w|v)\d{3}")
logger = getLogger(__name__)


def lyt_creation_procedure(gwaio):
    logger.info("Layout creation procedure started")
    output_file = sub(VERSION_REGEX, "001", cmds.file(q=True, sn=True))
    ok = True
    if Path(output_file).exists():
        ok = (
            QMessageBox.question(
                None,
                "Warning",
                f"The file {output_file} already exists, Do you want to overwrite it?",
            )
            == QMessageBox.Yes
        )
    if not ok:
        return

    logger.info("Find Cam file")
    camera_path = "C:/Users/emaag/Documents/hia/projects/DEMO_PROJECT/production/publish/templates/cam_master.ma"
    camera_file = return_file(camera_path, Path(camera_path).parent, "MA Files (*.ma)")
    if camera_file:
        logger.info(f"Cam found: {camera_file}")

    logger.info("Find audio file")
    audio_path = f"{Path(gwaio.task.server_path).parent}/animatic"
    audio_file = return_file(
        return_highest_file(VERSION_REGEX, audio_path, ".wav"),
        audio_path,
        "WAV Files (*.wav)",
    )
    if audio_file:
        logger.info(f"Audio found: {audio_file}")

    logger.info("Find assets file")
    assets = gwaio.task.assets.split(",")
    assets_data = list()
    for asset_code in assets:
        response = gwaio.plugin.async_find(
            "Asset", [["code", "is", asset_code]], ["code", "sg_asset_type"]
        )[0]
        asset_type = response.get("sg_asset_type")
        asset_name, asset_variant = asset_code.split("_")

        asset_path = f"{gwaio.plugin._server_root}/production/publish/assets/{asset_type}/{asset_name}/{asset_variant}/blocking"
        asset_file = return_file(
            return_highest_file(VERSION_REGEX, asset_path, ".ma"),
            asset_path,
            "MA Files (*.ma)",
        )
        if asset_file is None:
            logger.warning(f"Asset {asset_code} not found, skipping...")
            continue

        asset_ns = Path(asset_file).stem + "_rn0"
        assets_data.append((asset_file, asset_ns))
        logger.info(f"Asset will be {asset_file} with namespace {asset_ns}")

    logger.info("Find attributes project")
    input_file = None
    duration = gwaio.task.cut_duration
    start_frame = gwaio.plugin.attributes["start_frame"]
    fps = gwaio.plugin.dccs["maya"]["attributes"]["fps"]
    resolution = gwaio.plugin.attributes["resolution"]
    hierarchy_config = gwaio.plugin.dccs["maya"]["hierarchy"]
    image_plane = gwaio.plugin.dccs["maya"]["image_plane"]
    render_config = gwaio.plugin.dccs["maya"]["render_config"]
    color_management = gwaio.plugin.dccs["maya"]["attributes"]["color_management"]

    logger.info("Generate layout file")
    import_file(input_file)
    set_time_config(start_frame, duration, fps, resolution)
    import_audio(audio_file)
    create_hierarchy_from_dict(hierarchy_config)
    reference_files(assets_data, hierarchy_config)
    cam = import_camera(camera_file, hierarchy_config)
    if image_plane:
        import_image_plane(cam, image_plane)
    set_mh2_render(**render_config)
    set_color_management(color_management)
    save_maya(output_file)

def lyt_preview_procedure(gwaio, resolution: List[int] =[1920, 1080]):
    logger.info("Layout preview procedure started")
    
    logger.info("Find attributes version")
    duration = gwaio.task.cut_duration
    start_frame = gwaio.plugin.attributes["start_frame"]
    fps = gwaio.plugin.dccs["maya"]["attributes"]["fps"]
    resolution = resolution or gwaio.plugin.attributes["resolution"]
    playblast_cfg = gwaio.plugin.dccs["maya"]["playblast_config"]
    render_config = gwaio.plugin.dccs["maya"]["render_config"]
    color_management = gwaio.plugin.dccs["maya"]["attributes"]["color_management"]
    cam = "cam_master:cam_master"
    maya_file = Path(cmds.file(q=True, sn=True))
    output_path = maya_file.parent
    output_file = output_path / maya_file.stem
    playblast_cfg["filename"] = fspath(output_file.as_posix())
    if not cam:
        return

    logger.info("Attach playblast config data to playblast process")
    print(playblast_cfg)
    playblast_config = {
        "duration": duration,
        "start_frame": start_frame,
        "fps": fps,
        "color_management": color_management,
        "render_config": render_config,
        "playblast_cfg": playblast_cfg,
        "camera": cam,
    }

    try:
        output_file = run_playblast(
            **playblast_config,
            visible_huds=[],
            visible_objs=["polymeshes", "hos", "hud"],
            resolution=resolution,
        )
    except RuntimeError as e:
        print("Failed to create playblast due to {}".format(str(e)))

def lyt_publish_procedure(gwaio):
    logger.info("Layout publish procedure started")


def blk_creation_procedure(gwaio):
    logger.info("Blocking creation procedure started")

def blk_preview_procedure(gwaio):
    logger.info("Blocking preview procedure started")

def blk_publish_procedure(gwaio):
    logger.info("Blocking publish procedure started")

