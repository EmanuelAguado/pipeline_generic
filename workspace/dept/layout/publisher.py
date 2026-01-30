from pathlib import Path
from typing import TYPE_CHECKING
from logging import getLogger
from re import compile

from maya import cmds  # type: ignore

from pipe_utils import return_highest_file  # type: ignore
import resolver_utils  # type: ignore
from publisher.core import Check, Context, Extract  # type: ignore
from maya_utils import (  # type: ignore
    return_empty_transforms,
)
from maya_procedures import (  # type: ignore
    create_hierarchy_from_dict,
    return_asset_parent,
    return_root_nodes_from_reference,
    return_root_transform,
    # return_references_top,
    import_audio,
    export_cam,
    return_reference_file_and_ns,
)

if TYPE_CHECKING:
    import gwaio # type: ignore

logger = getLogger(__name__)

# [W] "CheckReferencedAssets": {} | Ninguna referencia sobrante/faltante
# [] "CheckAssetPathSchema": {} | path de referencia correctos
# [W] "CheckAssetsNameSpaces": {}, | namespaces correctos
# [W] "CheckAudioFile": {}, | audio correcto


class CheckAssetsNameSpaces(Check):
    # TODO: Falta comprobar si el namespace es correcto o no
    info = "Checks that all asset namespaces are correct."
    name = "Check asset namespace"

    def process(self, context: Context) -> None:
        self.assets = context.get_data("gwaio").task.assets.split(";")
        assets = context.get_data("gwaio").task.assets.split(";")
        camera_path = context.get_data("gwaio").plugin.dccs["maya"]["schema"][
            "camera_file"
        ]

        correct_ns = list()
        for rn in cmds.ls(references=True):
            if not cmds.referenceQuery(rn, il=True):
                continue
            current_ns = cmds.referenceQuery(rn, ns=True).split(":")[-1]
            target_path = cmds.referenceQuery(rn, filename=True, wcn=True)
            # if Path(target_path).name == Path(camera_path).name:
            #    continue
            correct_ns.append(current_ns)

        bad_ns = list()
        for ns in cmds.namespaceInfo(lon=True):
            if ns in [":", "UI", "shared"]:
                continue
            if ns not in correct_ns:
                bad_ns.append([ ns, ns])

        if bad_ns: 
            self.add_error(
                "Bad asset namespaces",
                "Some asset namespaces are incorrect.",
                bad_ns,
            )

    def fix_method(self):
        logger.debug("Fix method not implemented yet")
        #
            # row = return_row_from_schema_and_file(schema, target_path, self.config)
            # if ns_string is None:
            #     expected_ns = Path(target_path).stem
            # else:
            #     row["reference_file"] = Path(target_path).stem
            #     expected_ns = resolve_path_schema(row, ns_string, self.config)
            # if SeqMatch(None, current_ns, expected_ns).ratio() <= ratio:
            #     logger.debug(
            #         f"{ratio} is bigger than {SeqMatch(None, current_ns, expected_ns).ratio()}"
            #     )
            #     return f"{rn} namespace must be {expected_ns}, not {current_ns}", False

            # if cmds.referenceQuery(rn, ns=True) not in namespaces:
            #     return f"Reference {rn} has incorrect namespace", False


class CheckAudioFile(Check):
    name = "Check audio file"
    info = "Checks that the scene audio matches the expected audio file."

    def process(self, context: Context) -> None:
        self.expected_audio_schema = None
        self.expected_audio = None
        audio_path = f"{Path(context.get_data('gwaio').task.server_path).parent}/animatic"  # context.get_data("gwaio").plugin.dccs["maya"]["schema"]["audio_file"]
        self.expected_audio = return_highest_file(
            compile(context.get_data("gwaio").plugin.schema["version_regex"]),
            audio_path,
            ".wav",
        )

        if not self.expected_audio:
            self.add_error(
                "Missing audio file",
                "This file seems to be missing the audio.",
                [["Missing audio file", None]],
            )
            return

        for audio_node in cmds.ls(typ="audio", l=True):
            audio_maya_file = cmds.getAttr(f"{audio_node}.filename")
            if Path(self.expected_audio) == Path(audio_maya_file):
                return

        self.add_error(
            "Wrong audio file",
            f"Audio file should be {self.expected_audio}.",
            [["Wrong audio file", None]],
        )

    def fix_method(self):
        if self.expected_audio:
            import_audio(self.expected_audio)


class CheckEmptyTransforms(Check):
    name = "Check empty transforms"
    info = "Looks for empty transforms\n" "and if so, fixing will remove them."

    def process(self, context: Context) -> None:
        self.hierarchy_config = context.get_data("gwaio").plugin.dccs["maya"][
            "hierarchy"
        ]
        exclude = ["|persp", "|top", "|front", "|side"]
        shot_outliner = list(f"|{n}" for n in self.hierarchy_config.keys())

        self.empty_transforms = list(return_empty_transforms())
        self.empty_transforms = [
            n for n in self.empty_transforms if n not in shot_outliner
        ]
        if len(self.empty_transforms) != 0:
            all_empty_transforms = [[item, item] for item in self.empty_transforms]
            self.add_error(
                "There are empty transform nodes",
                "There are empty transform nodes",
                all_empty_transforms,
            )

    def fix_method(self):
        cmds.delete(self.empty_transforms)


class CheckResolution(Check):
    name = "Check resolution"
    info = "Check of the correct resolution."

    def process(self, context: Context) -> None:
        resolution = context.get_data("gwaio").plugin.attributes["resolution"]
        self.correct_resolution = (
            [float(resolution[0]), float(resolution[1])] if resolution else None
        )

        if self.correct_resolution[0] != cmds.getAttr("defaultResolution.width"):
            self.add_error(
                f"Bad resolution.",
                f"Correct resolution: {self.correct_resolution}.",
                [[f"Bad resolution. Correct resolution: {self.correct_resolution}", None]],
            )
        elif self.correct_resolution[1] != cmds.getAttr("defaultResolution.height"):
            self.add_error(
                f"Bad resolution.",
                f"Correct resolution: {self.correct_resolution}.",
                [[f"Bad resolution. Correct resolution: {self.correct_resolution}", None]],
            )

    def fix_method(self):
        cmds.setAttr("defaultResolution.width", self.correct_resolution[0], l=False)
        cmds.setAttr("defaultResolution.height", self.correct_resolution[1], l=False)


class CheckStartFrame(Check):
    name = "Check start frame"
    info = "Check of the first frame of the shot."

    def process(self, context: Context) -> None:
        start_frame = context.get_data("gwaio").plugin.attributes["start_frame"]
        self.correct_start_frame = float(start_frame) if start_frame else None
        error_start_frame = []
        if self.correct_start_frame is None:
            pass
        elif (
            not cmds.playbackOptions(q=True, min=True) == self.correct_start_frame
            or not cmds.playbackOptions(q=True, ast=True) == self.correct_start_frame
        ):
            error_start_frame.append(
                [f"Shot doesn't start at frame {self.correct_start_frame}.", None]
            )

        if error_start_frame:
            self.add_error(
                f"Shot doesn't start at frame {self.correct_start_frame}",
                f"Shot doesn't start at frame {self.correct_start_frame}",
                error_start_frame,
            )

    def fix_method(self):
        cmds.playbackOptions(e=True, min=self.correct_start_frame)
        cmds.playbackOptions(e=True, ast=self.correct_start_frame)


class CheckDuration(Check):
    name = "Check duration"
    info = "Check of the duration of the shot."

    def process(self, context: Context) -> None:
        duration = context.get_data("gwaio").task.cut_duration
        start_frame = context.get_data("gwaio").plugin.attributes["start_frame"]

        self.correct_duration = float(duration) if duration else None
        self.correct_start_frame = float(start_frame) if start_frame else None
        self.correct_end_frame = None
        if self.correct_duration is not None and self.correct_start_frame is not None:
            self.correct_end_frame = (
                self.correct_start_frame + self.correct_duration - 1
            )
        if (
            not cmds.playbackOptions(q=True, max=True) == self.correct_end_frame
            or not cmds.playbackOptions(q=True, aet=True) == self.correct_end_frame
        ):
            self.add_error(
                f"Incorrect end frame",
                f"Incorrect end frame",
                [
                    [
                        f"Incorrect end frame, the correct end frame is {self.correct_end_frame}.",
                        None,
                    ]
                ],
            )

    def fix_method(self):
        if self.correct_end_frame is None:
            return
        cmds.playbackOptions(e=True, max=self.correct_end_frame)
        cmds.playbackOptions(e=True, aet=self.correct_end_frame)


class CheckUnusedReferences(Check):
    name = "Check unused references"
    info = "Checks that there are no unloaded (disabled) references in the scene."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unloaded_references = []

    def process(self, context: Context) -> None:
        self.unloaded_references = []
        for ref_node in cmds.ls(type="reference") or []:
            if ref_node == "sharedReferenceNode":
                continue
            try:
                if not cmds.referenceQuery(ref_node, isLoaded=True):
                    self.unloaded_references.append(ref_node)
            except RuntimeError:
                continue

        if self.unloaded_references:
            error_list = [[ref_node, ref_node] for ref_node in self.unloaded_references]
            self.add_error(
                "Unused references",
                "There are unloaded references in the scene.",
                error_list,
            )

    def fix_method(self):
        for ref_node in self.unloaded_references:
            try:
                cmds.file(loadReference=ref_node)
            except RuntimeError:
                continue


class CheckFPS(Check):
    name = "Check FPS"
    info = f"Checks the correctframes per second."

    def process(self, context: Context) -> None:
        self.correct_fps = context.get_data("gwaio").plugin.dccs["maya"]["attributes"][
            "fps"
        ]

        dict_types = {
            "game": "15fps",
            "film": "24fps",
            "pal": "25fps",
            "ntsc": "30fps",
            "show": "48fps",
            "palf": "50fps",
            "ntscf": "60fps",
        }
        if self.correct_fps in dict_types.keys():
            pass
        elif self.correct_fps in dict_types.values():
            self.correct_fps = list(dict_types.keys())[
                list(dict_types.values()).index(self.correct_fps)
            ]

        if not cmds.currentUnit(q=True, t=True) == self.correct_fps:
            self.add_error(
                "Bad config FPS",
                f"Bad config FPS {self.correct_fps} > {cmds.currentUnit(q=True, t=True)}",
                [["Bad config FPS", "Bad config FPS"]],
            )

    def fix_method(self):
        cmds.currentUnit(t=self.correct_fps)


class CheckAssetHierarchy(Check):
    name = "Check asset hierarchy"
    info = "Checks that the asset hierarchy matches the expected hierarchy."

    def process(self, context: Context) -> None:
        self.hierarchy_config = context.get_data("gwaio").plugin.dccs["maya"][
            "hierarchy"
        ]
        exclude = ["|persp", "|top", "|front", "|side"]
        shot_outliner = list(self.hierarchy_config.keys())
        error_nodes = list()

        for node in cmds.ls(dag=True, l=True, typ="transform"):
            if node in exclude:
                continue
            parent = return_root_transform(node)
            if parent not in shot_outliner:
                error_nodes.append([node.split("|")[-1], node])

        if error_nodes:
            self.add_error(
                "Bad asset hierarchy",
                f"Nodes with wrong parent found.",
                error_nodes,
            )
            print(node, "<>", parent)

        create_hierarchy_from_dict(self.hierarchy_config)
        assemblies_cfg = self.hierarchy_config
        for rn in cmds.ls(references=True):
            logger.debug(f"Working on RN {rn}")
            path = cmds.referenceQuery(rn, f=True)
            parents = list(return_asset_parent(Path(path).stem, assemblies_cfg))
            self.root_nodes = return_root_nodes_from_reference(rn)
            logger.debug(f"The current root nodes of the RN are: {self.root_nodes}")
            logger.debug(f"The parent of the assets should be {', '.join(parents)}")
            error_nodes = list()
            for n in self.root_nodes:
                logger.debug(f"Working on root node {n} from reference {rn}")
                if (
                    all(not n.startswith(p) for p in parents)
                    or cmds.listRelatives(n, p=True) is None
                ):
                    error_nodes.append([f"{n} parent should be {', '.join(parents)}", n])
            if error_nodes:
                self.add_error(
                    f"Bad asset hierarchy - {rn}",
                    "Bad asset hierarchy",
                    error_nodes,
                )

    def fix_method(self):
        create_hierarchy_from_dict(self.hierarchy_config)
        assemblies_cfg = self.hierarchy_config
        for rn in cmds.ls(references=True):
            path = cmds.referenceQuery(rn, f=True)
            parents = list(return_asset_parent(Path(path).stem, assemblies_cfg))
            self.root_nodes = return_root_nodes_from_reference(rn)
            for n in self.root_nodes:
                logger.debug(n)
                if (
                    any(n.startswith(p) for p in parents)
                    and cmds.listRelatives(n, p=True) is not None
                ):
                    continue
                cmds.parent(n, parents[0])


class CheckReferencedAssets(Check):
    name = "Check referenced assets"
    info = "Checks that all referenced assets are correct in the shot."
    compulsory = False

    def process(self, context: Context) -> None:
        list_references_path = list()
        assets_bad_path = list
        for rn, file, ns, nodes in return_reference_file_and_ns():
            list_references_path.append(Path(file).as_posix())

        version_regex = compile(
            context.get_data("gwaio").plugin.schema["version_regex"]
        )
        assets = context.get_data("gwaio").task.assets.split(",")
        assets_missing = list()
        assets_unexpected = list()
        list_references_path_in_maya = list()
        for asset_code in assets:
            ctx = context.get_data("gwaio").plugin.async_find(
                "Asset", [["code", "is", asset_code]], ["code", "sg_asset_type"]
            )[0]
            # asset_type = ctx.get("sg_asset_type")
            asset_name, asset_variant = asset_code.split("_")
            ctx.update(
                {
                    "root": context.get_data("gwaio").plugin._server_root,
                    "asset_name": asset_name,
                    "variant_name": asset_variant,
                    "task_name": "modelBlocking",
                }
            )
            asset_path = resolver_utils.resolve(
                context.get_data("gwaio").plugin.dccs["maya"]["schema"]["asset_path_schema"],
                ctx,
            )
            # asset_path = f"{context.get_data('gwaio').plugin._server_root}/production/publish/assets/{asset_type}/{asset_name}/{asset_variant}/modelBlocking"
            asset_file = return_highest_file(version_regex, asset_path, ".ma")
            if asset_file:
                list_references_path_in_maya.append(Path(asset_file).as_posix())
            if not asset_file or Path(asset_file).as_posix() not in list_references_path:
                logger.warning(f"Asset {asset_code} not found...")
                print(f"Asset {asset_code} not found...")
                assets_missing.append([asset_code, asset_code])

        for file in list_references_path:
            if Path(file).as_posix() not in list_references_path_in_maya:
                assets_unexpected.append([Path(file).stem, Path(file).stem])

        if assets_missing:
            self.add_error(
                "Missing references",
                f"Missing reference",
                assets_missing,
            )
        if assets_unexpected:
            self.add_error(
                "Unexpected references or bad path",
                "Unexpected references or bad path",
                assets_unexpected,
            )

    def fix_method(self):
        # ns_string = self.config["maya.config.namespace_schema"]
        # assets = [
        #     a
        #     for a in self.assets
        #     if any(a["entity.Asset.code"] in f for f in self.missing)
        # ]
        # namespaces = list(yield_asset_namespaces(ns_string, assets, self.config))
        # asset_data = zip(self.missing, namespaces)

        # import_assets_from_file_and_ns(
        #     asset_data, self.config["maya.config.assemblies"]
        # )
        # for bad_ref in self.bad_refs:
        #     cmds.file(removeReference=True, rfn=cmds.referenceQuery(bad_ref, rfn=True))
        logger.debug("Fix not implemented yet")


class ExtractCamera(Extract):
    name = "Extract camera"
    info = "Extracts the camera from the scene."

    def process(self, context: Context) -> None:
        maya_publish_path = context.get_data("gwaio").plugin.work_to_publish(
            context.get_data("task")
        )[1]
        cam_name = "|cam|cam_master:CAM_MASTER|cam_master:cam_master"
        cam_out_name = resolver_utils.resolve(
            context.get_data("gwaio").plugin.dccs["maya"]["schema"][
                "camera_name_schema"
            ],
            context.get_data("gwaio").task.__dict__,
        )
        cam_output_file = Path(f"{maya_publish_path}/dmp_camera.abc")

        export_cam(
            cam_input_name=cam_name,
            cam_output_name=cam_out_name,
            output_file=cam_output_file,
            cam_grp="bcam",
        )