from fnmatch import fnmatch
from logging import getLogger
from os import fspath
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = getLogger(__name__)

from maya import cmds, mel # type: ignore
from maya.api.OpenMaya import MGlobal # type: ignore
from PySide6.QtWidgets import QFileDialog # type: ignore

from maya_utils import load_plugins  # type: ignore
import shotgun_api3 as sg3

VIEWPORT_SHOW_OPTIONS = {
    "hos": True,
    "hud": True,
    "polymeshes": True,
}

# Maya logging functions
def maya_error(message: str) -> None:
    MGlobal.displayError(message)

def maya_warning(message: str) -> None:
    MGlobal.displayWarning(message)

def maya_info(message: str) -> None:
    MGlobal.displayInfo(message)

def auto_retopology(target_object: str, target_faces: int = 5000) -> None:
    """
    Perform automatic retopology on the selected object.

    :param target_object: The name of the object to apply retopology to.
    :param target_faces: Approximate number of faces for the new topology.
    """
    if not cmds.objExists(target_object):
        raise ValueError(f"The object {target_object} does not exist in the scene.")

    # Select the object
    cmds.select(target_object)

    # Apply the Retopologize command
    retopo_node = cmds.polyRetopo(
        target_object,
        tfc=target_faces,
        trg=0  # 0: None, 1: X, 2: Y, 3: Z
    )
    cmds.delete(target_object, ch=True)
    maya_info(f"Retopology applied: {retopo_node}")

def create_hierarchy_from_dict(config: Dict[str, str]):
    for node in config:
        create_hierarchy(node)

def create_hierarchy(slug, parent=""):
    for x in slug.split("|"):
        if cmds.objExists(f"{parent}|{x}"):
            parent += f"|{x}"
            continue
        if parent == "":
            parent = cmds.createNode("transform", name=x)
        else:
            parent = cmds.createNode("transform", name=x, parent=parent)

def create_groups_and_controller(
    obj: str = None, 
) -> Tuple[str, str, str, str]:
    """
    Create groups and a controller for the imported object.

    :param obj: Name of the imported object.
    :return: Tuple containing names of the main group, model group, rig group, and controller.
    """
    obj = obj if obj else cmds.ls(sl=True,l=True)[0]
    if not cmds.objExists(obj):
        obj = cmds.group(empty=True, name=obj)
    model_grp = f"{obj}|model_grp"
    if not cmds.objExists(model_grp):
        model_grp = cmds.group(empty=True, name="model_grp", parent=obj)
        #cmds.parent(imported_obj_name, model_grp)
    rig_grp = f"{obj}|rig_grp"
    if not cmds.objExists(rig_grp):
        rig_grp = cmds.group(empty=True, name="rig_grp", parent=obj)
        #cmds.parent(imported_obj_name, rig_grp)
    bounding_box = cmds.exactWorldBoundingBox(obj)
    max_size = max(
        bounding_box[3] - bounding_box[0],
        bounding_box[4] - bounding_box[1],
        bounding_box[5] - bounding_box[2],
    )
    controller = cmds.circle(name="main_controller", normal=[0, 1, 0], radius=max_size * 0.5)[0]
    cmds.parent(controller, rig_grp)

    parent_constraint = cmds.parentConstraint(controller, model_grp, maintainOffset=True)
    scale_constraint = cmds.scaleConstraint(controller, model_grp, maintainOffset=True)
    
    cmds.parent(parent_constraint, controller)
    cmds.parent(scale_constraint, controller)
    
    print(f"Groups and controller created for {obj}.")
    return obj, model_grp, rig_grp, controller

def export_cam(cam_name: str):
    maya_name = Path(cmds.file(q=True, sn=True))
    output_path = Path(f"{maya_name.parent}/exports/{maya_name.stem}_{cam_name}_cam.fbx")
    output_path.parent.mkdir(exist_ok=True)
    load_plugins(["matrixNodes", "fbxmaya"])
    mel.eval("FBXExportCameras -v true")
    mel.eval("FBXProperty Export|IncludeGrp|Animation -v true")

    cmds.rename(cam_name, cam_name + "_temp")
    export_cam_transform = cmds.camera(n=cam_name)[0]
    cam_transform = cmds.listRelatives(cam_name + "_tempShape", p=True, f=True)[0]
    export_cam_transform = cmds.rename(export_cam_transform, cam_name)
    decompose_matrix_node = cmds.shadingNode("decomposeMatrix", asUtility=True)

    cmds.connectAttr(
        cam_transform + ".worldMatrix[0]",
        decompose_matrix_node + ".inputMatrix",
        force=True,
    )

    cmds.connectAttr(
        decompose_matrix_node + ".outputTranslate",
        export_cam_transform + ".translate",
        force=True,
    )

    cmds.connectAttr(
        decompose_matrix_node + ".outputRotate",
        export_cam_transform + ".rotate",
        force=True,
    )

    cam_shape = cmds.listRelatives(cam_transform, s=True, type="camera", f=True)[0]
    export_cam_shape = cmds.listRelatives(
        export_cam_transform, s=True, type="camera", f=True
    )[0]

    attrs = [
        ".lensSqueezeRatio",
        ".focusDistance",
        ".focalLength",
        ".fStop",
        ".centerOfInterest",
        ".cameraAperture",
    ]

    for tag in attrs:
        cmds.connectAttr(cam_shape + tag, export_cam_shape + tag, f=True)

    cmds.bakeResults(
        export_cam_transform,
        simulation=True,
        t=(
            cmds.playbackOptions(min=True, q=True),
            cmds.playbackOptions(max=True, q=True),
        ),
        sampleBy=1,
        oversamplingRate=1,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        controlPoints=False,
        shape=True,
    )

    cmds.select(cl=True)
    cmds.select(export_cam_transform)
    cmds.delete(decompose_matrix_node)
    cmds.disconnectAttr(cam_shape + tag, export_cam_shape + tag)
    for tag in attrs:
        try:
            cmds.disconnectAttr(cam_shape + tag, export_cam_shape + tag)
        except:
            pass

    cmds.delete(export_cam_transform, constructionHistory=True)
    cmds.delete(export_cam_shape, constructionHistory=True)

    cmds.file(
        output_path,
        f=True,
        options="v=0;",
        typ="FBX export",
        pr=False,
        es=True,
        sh=False,
    )
    try:
        cmds.delete(cam_name)
    except:
        pass

    cmds.rename(cam_name + "_temp", cam_name)

def image_to_blocking(obj_path,task_id):
    import maya.standalone as alone  # type: ignore
    alone.initialize()
    imported_obj_name = import_obj(obj_path)
    # auto_retopology(imported_obj_name, target_faces=500)
    create_groups_and_controller(imported_obj_name)
    cmds.file(rename={Path(obj_path).with_suffix('.ma')})
    cmds.file(save=True, type='mayaAscii', op='v=0', force=True)
    sg_change_status_task(task_id,'rdy')
    alone.uninitialize()

def import_file(file: Union[str, Path], parent: Union[str, None] = None):
    if file:
        cmds.file(file, o=True, f=True)
    else:
        cmds.file(new=True, f=True)

def import_audio(file_path: Union[str, Path], node_name: Union[str, None] = None):
    if not file_path:
        return
    for audio in list(cmds.ls(type="audio")):
        cmds.delete(audio)
    if not node_name:
        node_name = Path(file_path).stem
    audio_node = cmds.sound(
        o=cmds.playbackOptions(q=True, min=True), f=fspath(file_path), n=node_name
    )
    if not cmds.about(batch=True):
        gPlayBackSlider = mel.eval("$tmpVar=$gPlayBackSlider")
        cmds.timeControl(gPlayBackSlider, edit=True, sound=audio_node, ds=True)

def import_camera(cam_file: str, config: Dict[str, str]):
    cam_parent = next(return_asset_parent(Path(cam_file).stem, config), None)
    ref, cam_node = reference_file(cam_file, "", cam_parent)
    cam = [node for node in cam_node if node in cmds.ls(typ="camera")]
    if cam:
        set_renderable_camera(cam[0])
    return cam

def import_image_plane(camera: str, file: Union[str, Path]):
    image_plane = cmds.imagePlane(camera=camera[0], fn=fspath(file))
    cmds.setAttr(image_plane[0] + ".fit", 1)
    cmds.setAttr(image_plane[0] + ".colorSpace", "sRGB", type="string")
    cmds.setAttr(image_plane[0] + ".depth", 100000)
    return image_plane

def import_obj(output_obj_path: str) -> Optional[str]:
    """
    Import an OBJ file into Maya and rename it based on its file name.

    :param output_obj_path: Path to the OBJ file.
    :return: Name of the imported object in Maya, or None if the file does not exist.
    """
    if not Path(output_obj_path).exists():
        maya_error("OBJ file not found.")
        return None

    stem_name = Path(output_obj_path).stem
    transform_name = "_".join(stem_name.split("_")[2:4])
    
    cmds.file(output_obj_path, i=True, type="OBJ")
    imported_obj_name = cmds.ls(typ="transform")[0]
    renamed_obj_name = cmds.rename(imported_obj_name, transform_name)
    maya_info(f"Imported mesh renamed to: {renamed_obj_name}")
    return renamed_obj_name

def reference_files(objects: List[str], config: Dict[str, str]):
    for asset in objects:
        path, ns = asset
        if path is None:
            continue
        parent = next(return_asset_parent(Path(path).stem, config), None)
        reference_file(path, ns, parent)

def reference_file(
    file: Union[str, Path], namespace: Union[str, None], parent: Union[str, None] = None
):
    try:
        namespace = namespace or Path(file).stem
        ref = cmds.file(fspath(file), r=True, namespace=namespace, force=True)
        nodes = cmds.referenceQuery(ref, nodes=True, dp=True)
        ref_node = cmds.referenceQuery(ref, referenceNode=True)
        cmds.lockNode(ref_node, l=False)
        tokens = cmds.referenceQuery(ref_node, ns=True).split("_")
        new_ref_node_name = "_".join(t for t in tokens[:-1]) + "_" + tokens[-1].upper()
        new_ref_node = cmds.rename(ref_node, new_ref_node_name)
        cmds.lockNode(new_ref_node, l=True)
        if parent is not None:
            cmds.parent(nodes[0], parent)
        return ref, nodes
    except Exception as e:
        logger.warning(str(e))

def return_asset_parent(node, assemblies_config: Dict[str, str]):
    i = completed = 0
    while len(assemblies_config) >= completed:
        for parent, regex_list in assemblies_config.items():
            if len(regex_list) < i + 1:
                completed += 1
                continue
            regex = regex_list[i]

            if fnmatch(node, regex):
                try:
                    yield cmds.ls(parent, l=True)[0]
                except IndexError as e:
                    logger.warning(f"There is not a node called {parent}")
                    raise (e)
        i += 1

def return_config_viewport(**kwargs):
    for k in kwargs.keys():
        yield {k: cmds.getAttr(f"hardwareRenderingGlobals.{k}")}

def return_model_panel_with_cam(cam: str):
    for mp in cmds.getPanel(type="modelPanel") or list():
        camera = cmds.modelEditor(mp, q=True, cam=True)
        camera = cmds.listRelatives(camera, c=True, f=True) or [camera]
        camera = camera[0]
        logger.debug(f"Model {mp} has camera {camera}, and target it {cam}")
        if cam in camera:
            return mp
        
def return_file(file_path, dir, ext):
    file_path = Path(file_path or "")
    dir = dir if Path(dir).exists() else ""
    if file_path.is_file():
        return file_path
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select File",
        dir,
        ext,
    )

    if not file_path:
        return None
    return file_path

def return_top_refs():
    for rn in cmds.ls(references=True, l=True):
        if cmds.referenceQuery(rn, rfn=True, tr=True) == rn:
            return rn

def return_model_panel():
    """Attempts to return current model panel."""
    model_panels = cmds.getPanel(type="modelPanel")
    with_focus = cmds.getPanel(withFocus=True)
    if model_panels is None:
        return None
    elif len(model_panels) == 1:
        return model_panels[0]
    elif with_focus in model_panels:
        return with_focus
    else:  # get the largest model panel
        current_area = 0
        current_panel = ""
        for p in model_panels:
            w = cmds.control(p, q=True, w=True)
            h = cmds.control(p, q=True, h=True)
            area = w * h
            if current_area < area:
                current_area = area
                current_panel = p
    return current_panel

def return_panel_visible_items():
    model_panel = return_model_panel()
    if model_panel is None:
        yield dict()
    else:
        for k in VIEWPORT_SHOW_OPTIONS.keys():
            yield {k: cmds.modelEditor(model_panel, q=True, **{k: True})}

def return_root_nodes_from_reference(rn: str) -> List[str]:
    nodes = cmds.ls(cmds.referenceQuery(rn, nodes=True, dp=True), l=True, dag=True)
    parents = [(cmds.listRelatives(n, p=True, f=True) or ["|"])[0] for n in nodes]
    return [n for n, p in zip(nodes, parents) if p not in nodes]

def run_playblast(
    start_frame: int,
    duration: int,
    fps: str,
    color_management: str,
    render_config: Dict[str, Any],
    playblast_cfg: Dict[str, Any],
    camera: str,
    visible_huds: Optional[List[str]] = None,
    visible_objs: List[str] = list(),
    ffmpeg_config: Dict[str, Dict[str, Any]] = None,
    resolution: List[int] = [1920, 1080],
):
    logger.info("Preparing playblast process")
    set_time_config(start_frame, duration, fps, resolution)
    if not cmds.about(batch=True):
        set_hud_size(20)
    set_hud(visible_huds)
    
    if cmds.about(batch=True):
        for cam in cmds.ls(cameras=True):
            cmds.setAttr(f"{cam}.renderable", False)
        cmds.setAttr(f"{camera}.renderable", True)
        set_timeline_progress()

    logger.info(f"Setting camera {camera}")
    panel_candidate = return_model_panel_with_cam(camera)
    if panel_candidate is not None:
        logger.debug(f"Setting active model panel {panel_candidate}")
        cmds.setFocus(panel_candidate)
    elif not cmds.about(batch=True):
        cmds.lookThru(camera)

    logger.info("Settings viewport config before playblast.")
    shown_objs = {k: v for d in return_panel_visible_items() for k, v in d.items()}
    vp2 = {k: v for d in return_config_viewport(**render_config) for k, v in d.items()}
    objs_to_show = {k: False for k in shown_objs}
    objs_to_show.update({k: True for k in visible_objs})
    set_vp2_shown_objects(**objs_to_show)
    logger.debug(f"Setting viewport config before playblast.")
    set_mh2_render(**render_config)
    set_color_management(color_management)

    audio = next((f for f in cmds.ls(type="audio", l=True)), None)

    if audio is not None:
        playblast_cfg["sound"] = audio

    cmds.select(cl=True)
    logger.info(f"Launching playblast with name: {playblast_cfg['filename']}")
    logger.debug(f"Playblast config is: {playblast_cfg}")
    cmds.playblast(**playblast_cfg)
    logger.info(f"Launching playblast done: {playblast_cfg['filename']}")

    logger.debug(f"Setting back viewport config after playblast")
    set_mh2_render(**vp2)
    set_vp2_shown_objects(**shown_objs)
    # take_snapshot(Path(playblast_cfg["filename"]).with_suffix(".jpg"))
    return playblast_cfg["filename"]

def save_maya(output_file: Union[str, Path] = None):
    if output_file is None:
        output_file = return_current_maya()
    Path(output_file).parent.mkdir(exist_ok=True, parents=True)
    cmds.file(rename=output_file)
    cmds.file(save=True, type="mayaAscii", op="v=0", force=True)
        
def set_hud(visible_huds: Optional[List[str]] = None):
    # if None, don't modify HUDs, else, show the ones in the list and hide the rest
    if visible_huds is None:
        return
    for hud in cmds.headsUpDisplay(listHeadsUpDisplays=True) or []:  # fix standalone
        if hud in visible_huds:
            cmds.headsUpDisplay(hud, e=True, vis=True, lfs="large", dfs="large")
        else:
            cmds.headsUpDisplay(hud, e=True, vis=False)

def set_hud_size(size: int = 20):
    cmds.displayPref(fm=2)
    cmds.displayPref(sfs=size)
    cmds.displayPref(dfs=size)
    cmds.menuSetPref(saveAll=True)
    mel.eval('syncPreferencesOptVars "syncOptToCurrent";syncGlobalOptVars;')

def set_time_config(
    start_frame: int,
    duration: int,
    fps: Union[str, int],
    resolution: List[int],
):
    cmds.currentUnit(t=fps)
    cmds.playbackOptions(e=True, min=int(start_frame))
    cmds.playbackOptions(e=True, ast=int(start_frame))
    cmds.playbackOptions(e=True, max=str(int(start_frame) + int(duration) - 1))
    cmds.playbackOptions(e=True, aet=str(int(start_frame) + int(duration) - 1))
    cmds.setAttr("defaultResolution.width", resolution[0], l=False)
    cmds.setAttr("defaultResolution.height", resolution[1], l=False)

def set_timeline_progress():
    logger.debug("Setting up timeline progress callback.")
    exp_string = (
        'print("start: {} min: {} ");float $curr=`currentTime -q`;'
        'print("curr_time: " + $curr + " max_time: {} end: {} Progress: {}%\\n");'.format(
            cmds.playbackOptions(q=True, ast=True),
            cmds.playbackOptions(q=True, min=True),
            cmds.playbackOptions(q=True, max=True),
            cmds.playbackOptions(q=True, aet=True),
            cmds.currentTime(q=True) / cmds.playbackOptions(q=True, aet=True) * 100,
        )
    )
    exp_name = "on_frame_change_expression"
    if not exp_name in cmds.ls(type="expression"):
        e = cmds.expression(n=exp_name, o="persp", ae=True, s=exp_string)

    return exp_name

def set_color_management(otn: str = "sRGB"):
    cmds.colorManagementPrefs(e=True, cme=True)
    cmds.colorManagementPrefs(e=True, ote=True)
    cmds.colorManagementPrefs(e=True, otc=True)
    cmds.colorManagementPrefs(e=True, otn=otn)

def set_vp2_shown_objects(**kwargs):
    model_panel = return_model_panel()
    if model_panel is None:
        return
    else:
        for k, v in VIEWPORT_SHOW_OPTIONS.items():
            value = kwargs.get(k, v)
            cmds.modelEditor(model_panel, e=True, **{k: value})

def set_mh2_render(**config):
    cmds.setAttr("defaultRenderGlobals.ren", "mayaHardware2", type="string")
    for key, value in config.items():
        cmds.setAttr(f"hardwareRenderingGlobals.{key}", value)

def set_renderable_camera(camera_shape: str = "persp"):
    try:
        panel_name = cmds.playblast(activeEditor=True).split("|")[-1]
        cmds.lookThru(panel_name, camera_shape)
    except:
        pass

    for cam in cmds.ls(typ="camera"):
        if cam != camera_shape:
            cmds.setAttr(f"{cam}.renderable", False)
    cmds.setAttr(camera_shape + ".renderable", True)

def sg_change_status_task(task_id, status):
    ...
#     sg = sg3.Shotgun(
#         SHOTGRID_URL,
#         script_name=SHOTGRID_SCRIPT_NAME,
#         api_key=SHOTGRID_API_KEY,
#     )
#     sg.update("Task", task_id, {"sg_status_list": status})
#     maya_info(f"Status Task {task_id} changed: {status}")

#     sg.close()
