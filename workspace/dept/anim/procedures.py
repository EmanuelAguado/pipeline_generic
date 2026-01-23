from logging import getLogger
from pathlib import Path
from re import compile, sub
from shutil import copy2
from typing import TYPE_CHECKING, List
from os import fspath

from PySide6.QtWidgets import QMessageBox  # type: ignore
from maya import cmds  # type: ignore

from pipe_utils import return_highest_file  # type: ignore
from maya_procedures import (  # type: ignore
    import_file,
    import_audio,
    import_cam,
    create_hierarchy_from_dict,
    set_color_management,
    set_hud,
    import_image_plane,
    reference_files,
    reference_update,
    return_file,
    run_playblast,
    set_mh2_render,
    set_time_config,
    save_maya,
)

if TYPE_CHECKING:
    import gwaio

logger = getLogger(__name__)


def blk_creation_procedure(gwaio):
    logger.info("First version creation started")
    output_file = sub(
        gwaio.plugin.schema["version_regex"], "001", cmds.file(q=True, sn=True)
    )
    version_regex = compile(gwaio.plugin.schema["version_regex"])
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

    logger.info("Find previous task file")
    prev_task_path = gwaio.task.prev_task_server
    prev_file_path = return_file(
        return_highest_file(version_regex, prev_task_path, ".ma"),
        prev_task_path,
        "MA Files (*.ma)",
    )

    logger.info(f"The base file will be {prev_file_path}")
    if prev_file_path is None:
        return
    
    copy2(prev_file_path, output_file)
    cmds.file(output_file, o=True, f=True)

    if gwaio.task.name == "blocking":
        logger.info("Find Cam file")
        cam_file = return_file(
            Path(f"{gwaio.task.prev_task_server}/dmp_camera.abc").as_posix(),
            prev_task_path,
            "ABC Files (*.abc)",
        )
        if cam_file:
            logger.info(f"Cam found: {cam_file}")
        else:
            logger.warning("No cam found")
    # TODO: RENAME CAMERA

    logger.info("Find audio file")
    audio_path = f"{Path(gwaio.task.server_path).parent}/animatic"
    audio_file = return_file(
        return_highest_file(version_regex, audio_path, ".wav"),
        audio_path,
        "WAV Files (*.wav)",
    )
    if audio_file:
        logger.info(f"Audio found: {audio_file}")

    #remove camera reference
    import_cam(cam_file)
    import_audio(audio_file)

    logger.info("Updating the rigs for each maya file")
    assets = gwaio.task.assets.split(",")
    for asset_code in assets:
        response = gwaio.plugin.async_find(
            "Asset", [["code", "is", asset_code]], ["code", "sg_asset_type"]
        )[0]
        asset_type = response.get("sg_asset_type")
        asset_name, asset_variant = asset_code.split("_")
        asset_path = f"{gwaio.plugin._server_root}/production/publish/assets/{asset_type}/{asset_name}/{asset_variant}/rigging"
        asset_file = return_file(
            return_highest_file(version_regex, asset_path, ".ma"),
            asset_path,
            "MA Files (*.ma)",
        )
        if asset_file is None:
            logger.warning(f"Asset {asset_code} not found, skipping...")
            continue

        old_path = f"{gwaio.plugin._server_root}/production/publish/assets/{asset_type}/{asset_name}/{asset_variant}"
        logger.info(f"Updating asset {asset_code} from {old_path} to {asset_file}")
        reference_update(old_path, asset_file)
        logger.info(f"Asset {asset_code} updated successfully")

    save_maya(output_file)



def blk_preview_procedure(gwaio, resolution: List[int] = [1920, 1080]):
    logger.info("Blocking preview procedure started")

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


def blk_publish_procedure(gwaio):
    logger.info("Blocking publish procedure started")

    