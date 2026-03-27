import fnmatch
from logging import getLogger
from pathlib import Path
from re import compile, sub
from shutil import copy2
from typing import TYPE_CHECKING, List
from os import fspath

from PySide6.QtWidgets import QMessageBox  # type: ignore
from maya import cmds  # type: ignore

from pipe_utils import return_highest_file  # type: ignore
import resolver_utils  # type: ignore
from maya_procedures import (  # type: ignore
    import_audio,
    import_cam,
    export_cache,
    is_correct_task,
    reference_update,
    return_file,
    return_reference_file_and_ns,
    return_root_nodes_from_reference,
    run_playblast,
    save_maya,
)

if TYPE_CHECKING:
    import gwaio # type: ignore

logger = getLogger(__name__)


@is_correct_task("blocking", "refine", "fix", "bake")
def anim_creation_procedure(gwaio):
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

        # remove camera reference
        logger.info(f"Importing bake camera: {cam_file}")
        import_cam(cam_file)
        logger.debug(f"Importing audio file: {audio_file} | node name: {audio_node_name}")
        import_audio(audio_file, audio_node_name)

        logger.info("Removing layout camera")
        cam_name = "cam_MASTER"
        rn, file, ns, nodes = list(return_reference_file_and_ns(rn=cam_name))[0]
        cmds.file(file, importReference=True)
        for n in nodes:
            try:
                cmds.delete(n)
            except:
                pass
        try:
            cmds.delete("|cam")
        except:
            pass
        cmds.namespace(removeNamespace=ns.strip(":"))
        cmds.rename("|bcam", "cam")

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

@is_correct_task("blocking", "refine", "fix")
def anim_preview_procedure(gwaio, resolution: List[int] = [1920, 1080]):
    logger.info("Anim preview procedure started")
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

@is_correct_task("bake")
def bak_export_caches_procedure(gwaio):
    def return_cache_path(node: str, cache_type: str) -> str:
        _, asset_type, *_, node_name = node.split("|")
        name = node_name.split(":")[1]
        ma_path = Path(cmds.file(q=True, sn=True))
        output_file = Path(
            ma_path.parent,
            f"dmp_{asset_type}_{name}.{cache_type}",
        ).as_posix()
        return output_file

    logger.info("Bake export caches procedure started")

    seen = list()
    result = list()
    for rn in cmds.ls(references=True):
        if not cmds.referenceQuery(rn, il=True):
            logger.debug(f"The reference {rn} is not load")
            continue
        file_path = cmds.referenceQuery(rn, f=True, wcn=True)
        if not "/rigging/" in file_path:
            continue
        roots = return_root_nodes_from_reference(rn)
        root = roots[0] if roots else None
        if root in seen:
            continue
        seen.append(root)
        output_file = return_cache_path(root, "abc")
        result += export_cache(root, output_file=output_file)

@is_correct_task("bake")
def bak_import_caches_procedure(gwaio):
    def return_cache_path(node: str, cache_type: str) -> str:
        _, asset_type, *_, node_name = node.split("|")
        name = node_name.split(":")[1]
        ma_path = Path(cmds.file(q=True, sn=True))
        output_file = Path(
            ma_path.parent,
            f"dmp_{asset_type}_{name}.{cache_type}",
        ).as_posix()
        return output_file

    logger.info("Bake import caches procedure started")

    seen = list()
    result = list()
    for rn in cmds.ls(references=True):
        if not cmds.referenceQuery(rn, il=True):
            logger.debug(f"The reference {rn} is not load")
            continue
        file_path = cmds.referenceQuery(rn, f=True, wcn=True)
        if not "/rigging/" in file_path:
            continue
        roots = return_root_nodes_from_reference(rn)
        root = roots[0] if roots else None
        if root in seen:
            continue
        seen.append(root)
        output_file = return_cache_path(root, "abc")
        result += import_cache(root, output_file=output_file)

def import_ref_cache_from_selection(display_dialog: bool = False):
    logger.info("Importing caches")
    seen = list()
    result = list()
    for node in cmds.ls(sl=True, l=True):
        if not cmds.referenceQuery(node, inr=True):
            logger.debug(f"The node {node} doesn't belong to a reference")
            continue
        roots = return_root_nodes_from_reference(node)
        root = roots[0] if roots else None
        if root in seen:
            continue

        rn = cmds.referenceQuery(node, rfn=True)
        old_file = cmds.referenceQuery(rn, f=True, wcn=True)
        old_nodes = cmds.referenceQuery(rn, n=True, dp=True)

        if not "/rig/" in old_file:
            continue
        # logger.info(f"Swapping reference {old_file}")
        new_path = Path(old_file).parent.as_posix().replace("rig", "shad")
        asset_file = return_highest_file(recomp("(?<=u|v)[0-9]{4}"), new_path, ".ma")
        if asset_file is None:
            logger.warning(
                f"Failed to find shading file for reference {rn}, {old_file}"
            )
            continue
        # TODO: check if there is cache files for the shading file, if not log warning        
        rn_version = rn.split("_RN")[-1]
        asset_ns = Path(asset_file).stem + f"_rn{rn_version}"
        asset_ns = validate_namespace(asset_ns)
        root_rig = cmds.listRelatives(old_nodes[0], f=True)[0]
        ref_node = replace_reference(asset_file.as_posix(), rn, asset_ns)
        root_shd = return_root_nodes_from_reference(
            cmds.referenceQuery(ref_node, n=True)[0]
        )[0]

        # logger.info(f"Swap reference success {root_rig} -> {root_shd}")
        seen.append(root)

        result += mago_import_caches(root_shd, root_rig)

    if result and display_dialog:
        QMessageBox.information(
            None,
            "Processed files" + " " * 239,
            "List of processed files:\n" + "\n".join(result),
        )  # QMessageBox no ajusta su tamaño al texto ni hay forma de forzarlo
    return result