from logging import getLogger
from pathlib import Path
from re import compile, sub
from typing import TYPE_CHECKING, List
from os import fspath

from PySide6.QtWidgets import QMessageBox  # type: ignore
from maya import cmds  # type: ignore

from pipe_utils import return_highest_file  # type: ignore
import resolver_utils  # type: ignore
from maya_procedures import (  # type: ignore
    import_file,
    import_audio,
    import_cam,
    is_correct_task,
    export_cam,
    create_hierarchy_from_dict,
    set_color_management,
    import_image_plane,
    reference_files,
    reference_update,
    return_reference_file_and_ns,
    return_file,
    run_playblast,
    set_mh2_render,
    set_time_config,
    save_maya,
)

if TYPE_CHECKING:
    import gwaio  # type: ignore

logger = getLogger(__name__)

@is_correct_task("layout")
def lyt_creation_procedure(gwaio, shot_file=None):
    logger.info("Layout creation procedure started")
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

    logger.info("Find Cam file")
    camera_path = gwaio.plugin.dccs["maya"]["schema"]["camera_file"]
    camera_file = return_file(camera_path, Path(camera_path).parent, "MA Files (*.ma)")
    if camera_file:
        logger.info(f"Cam found: {camera_file}")

    logger.info("Find audio file")
    audio_path = f"{Path(gwaio.task.server_path).parent}/animatic"
    audio_file = return_file(
        return_highest_file(version_regex, audio_path, ".wav"),
        audio_path,
        "WAV Files (*.wav)",
    )
    audio_node_name = resolver_utils.resolve(
        gwaio.plugin.dccs["maya"]["schema"]["audio_name_schema"], gwaio.task.__dict__
    )
    if audio_file:
        logger.info(f"Audio found: {audio_file}")

    logger.info("Find assets file")
    assets = gwaio.task.assets.split(",")
    assets_data = list()
    for asset_code in assets:
        ctx = gwaio.plugin.async_find(
            "Asset", [["code", "is", asset_code]], ["code", "sg_asset_type"]
        )[0]
        asset_name, asset_variant = asset_code.split("_")
        task_name = "modelBlocking" if ctx.get("sg_asset_type") != "en" else "blockingDressing"
        
        ctx.update(
            {
                "root": gwaio.plugin._server_root,
                "asset_name": asset_name,
                "variant_name": asset_variant,
                "task_name": task_name,
            }
        )
        asset_path = resolver_utils.resolve(
            gwaio.plugin.dccs["maya"]["schema"]["asset_path_schema"],
            ctx,
        )
        asset_file = return_file(
            return_highest_file(version_regex, asset_path, ".ma"),
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
    input_file = shot_file
    duration = gwaio.task.cut_duration
    start_frame = gwaio.plugin.attributes["start_frame"]
    fps = gwaio.plugin.dccs["maya"]["attributes"]["fps"]
    resolution = gwaio.plugin.attributes["resolution"]
    hierarchy_config = gwaio.plugin.dccs["maya"]["hierarchy"]
    image_plane = gwaio.plugin.dccs["maya"]["image_plane"]
    render_config = gwaio.plugin.dccs["maya"]["render_config"]
    color_management = gwaio.plugin.dccs["maya"]["attributes"]["color_management"]

    logger.info("Generate layout file")
    logger.debug(f"Import template file: {input_file}")
    import_file(input_file)
    if input_file:
        logger.info(f"Template file imported: {input_file}")
        cmds.delete(cmds.ls(type="audio") or [])
    logger.debug(f"Setting time config: {start_frame}, {duration}, {fps}, {resolution}")
    set_time_config(start_frame, duration, fps, resolution)
    logger.debug(f"Importing audio file: {audio_file} | node name: {audio_node_name}")
    import_audio(audio_file, audio_node_name)
    logger.debug(f"Creating hierarchy: {hierarchy_config}")
    create_hierarchy_from_dict(hierarchy_config)
    if input_file:
        new_assets_data = list()
        existing_asset_path = [Path(a[1]).as_posix() for a in return_reference_file_and_ns(False)]
        for asset_file, asset_ns in assets_data:
            old_path = Path(asset_file).parent
            logger.info(f"Updating asset {asset_ns} from {old_path} to {asset_file}")
            reference_update(old_path, asset_file)
            logger.info(f"Asset {asset_ns} updated successfully")

        for asset_file, asset_ns in assets_data:
            if not Path(asset_file).as_posix() in existing_asset_path:
                new_assets_data.append((asset_file, asset_ns))
        reference_files(new_assets_data, hierarchy_config)

        for asset_file in existing_asset_path:
            if "cam_master" in Path(asset_file).stem:
                continue
            if not Path(asset_file).as_posix() in [Path(a[0]).as_posix() for a in assets_data]:
                logger.info(f"Removing asset reference {asset_file} as it's not in the current shot")
                cmds.file(asset_file, removeReference=True)
                logger.info(f"Asset reference {asset_file} removed successfully")

    else:
        logger.debug("reference files:")
        reference_files(assets_data, hierarchy_config)
        cam = import_cam(camera_file, hierarchy_config)
        if image_plane:
            import_image_plane(cam, image_plane)
    set_mh2_render(**render_config)
    set_color_management(color_management)
    save_maya(output_file)


@is_correct_task("layout")
def lyt_preview_procedure(gwaio, resolution: List[int] = [1920, 1080]):
    logger.info("Layout preview procedure started")
    logger.info("Find attributes version")
    duration = gwaio.task.cut_duration
    start_frame = gwaio.plugin.attributes["start_frame"]
    fps = gwaio.plugin.dccs["maya"]["attributes"]["fps"]
    resolution = resolution or gwaio.plugin.attributes["resolution"]
    playblast_cfg = gwaio.plugin.dccs["maya"]["playblast_config"]
    playblast_viewport_cfg = gwaio.plugin.dccs["maya"]["playblast_viewport_config"]
    playblast_camera_cfg = gwaio.plugin.dccs["maya"]["playblast_camera_config"]
    render_config = gwaio.plugin.dccs["maya"]["render_config"]
    color_management = gwaio.plugin.dccs["maya"]["attributes"]["color_management"]
    if gwaio.task.name == "layout":
        cam = "cam_master:cam_master"
    else:
        cam = resolver_utils.resolve(
            gwaio.plugin.dccs["maya"]["schema"]["camera_name_schema"],
            gwaio.task.__dict__,
        )

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
            playblast_viewport_cfg=playblast_viewport_cfg,
            playblast_camera_cfg=playblast_camera_cfg,
            resolution=resolution,
        )
    except RuntimeError as e:
        print("Failed to create playblast due to {}".format(str(e)))


@is_correct_task("layout")
def lyt_export_camera_procedure(gwaio):
    logger.info("Layout export camera procedure started")
    maya_publish_path = gwaio.plugin.work_to_publish(gwaio.task.serialize())[1]
    cam_name = "|cam|cam_master:CAM_MASTER|cam_master:cam_master"
    cam_out_name = resolver_utils.resolve(
        gwaio.plugin.dccs["maya"]["schema"]["camera_name_schema"], gwaio.task.__dict__
    )
    cam_output_file = Path(f"{maya_publish_path}/dmp_camera.usd")
    export_cam(
        cam_input_name=cam_name,
        cam_output_name=cam_out_name,
        output_file=cam_output_file,
        cam_grp="bcam",
    )


@is_correct_task("layout")
def lyt_import_camera_procedure(gwaio):
    logger.info("Layout import camera procedure started")
    maya_publish_path = gwaio.plugin.work_to_publish(gwaio.task.serialize())[1]
    cam_output_file = Path(f"{maya_publish_path}/dmp_camera.usd")
    import_cam(cam_output_file)


@is_correct_task("layout")
def lyt_clean_camera_procedure(gwaio):
    logger.info("Layout clean camera procedure started")
    cmds.delete("|bcam")
