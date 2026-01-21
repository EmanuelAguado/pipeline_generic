from pathlib import Path
from typing import TYPE_CHECKING
from logging import getLogger

from maya import cmds  # type: ignore

import maya_publisher  # type: ignore
from pipe_utils import return_highest_file  # type: ignore
from publisher.core import Check, Context, Extract # type: ignore
from maya_procedures import ( # type: ignore
    create_hierarchy_from_dict,
    return_asset_parent,
    return_root_nodes_from_reference,
    # return_top_refs,
    import_audio,
    export_cam,
)
if TYPE_CHECKING:
    import gwaio

logger = getLogger(__name__)

# [W] "CheckReferencedAssets": {},
# [] "CheckAssetPathSchema": {},
# [W] "CheckAssetsNameSpaces": {},
# [ ]  Ninguna referencia sobrante
# [ ]  path de referencia correctos

class CheckAssetsNameSpaces(Check):
    #TODO
    name = "Check asset namespace"
    active = False

    def check(self):
        self.assets = gwaio.task.assets.split(";")

        # ns_string = self.config["maya.config.namespace_schema"]
        # ratio = self.config["maya.config.checks.similarity_ratio"]
        # schema = self.config["context.entities"]["Asset"]
        camera_path = gwaio.plugin.dccs["maya"]["schema"]["camera_file"]

        for rn in cmds.ls(references=True):
            if not cmds.referenceQuery(rn, il=True):
                continue
            current_ns = cmds.referenceQuery(rn, ns=True).split(":")[-1]
            target_path = cmds.referenceQuery(rn, filename=True, wcn=True)

            if Path(target_path).name == Path(camera_path).name:
                continue
            
            logger.debug("Check not implemented yet")
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_audio_schema = None
        self.expected_audio = None

    def process(self, context: Context) -> None:
        audio_path = f"{Path(gwaio.task.server_path).parent}/animatic" #gwaio.plugin.dccs["maya"]["schema"]["audio_file"]
        self.expected_audio = return_highest_file(gwaio.plugin.schema["version_regex"], audio_path, ".wav")

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


class CheckResolution(Check):
    name = "Check resolution"
    info = (
        "Check of the resolution of the shot.\n"
        f"The resolution of the shot must be {gwaio.plugin.attributes['resolution']}."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        resolution = gwaio.plugin.attributes['resolution']

        self.correct_resolution = float(resolution) if resolution else None

    def process(self, context: Context) -> None:
        error_resolution = []
        if self.correct_resolution is None:
            pass
        elif (
            not cmds.playbackOptions(q=True, min=True) == self.correct_resolution
            or not cmds.playbackOptions(q=True, ast=True) == self.correct_resolution
        ):
            error_resolution.append(
                [f"Shot doesn't start at frame {self.correct_start_frame}.", None]
            )

        if error_resolution:
            self.add_error(
                f"Shot doesn't start at frame {self.correct_start_frame}",
                f"Shot doesn't start at frame {self.correct_start_frame}",
                error_resolution,
            )

    def fix_method(self):
        cmds.setAttr("defaultResolution.width", self.correct_resolution[0], l=False)
        cmds.setAttr("defaultResolution.height", self.correct_resolution[1], l=False)


class CheckStartFrame(Check):
    name = "Check start frame"
    info = (
        "Check of the first frame of the shot.\n"
        f"The first frame of the shot must be frame {gwaio.plugin.attributes['start_frame']}."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_frame = gwaio.plugin.attributes['start_frame']

        self.correct_start_frame = float(start_frame) if start_frame else None

    def process(self, context: Context) -> None:
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
    info = (
        "Check of the duration of the shot.\n"
        f"The duration of the shot must be {gwaio.task.cut_duration}."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        duration = gwaio.task.cut_duration
        start_frame = gwaio.plugin.attributes["start_frame"]

        self.correct_duration = float(duration) if duration else None
        self.correct_start_frame = float(start_frame) if start_frame else None
        self.correct_end_frame = None
        if self.correct_duration is not None and self.correct_start_frame is not None:
            self.correct_end_frame = self.correct_start_frame + self.correct_duration - 1

    def process(self, context: Context) -> None:
        error_duration = []
        if self.correct_end_frame is None:
            pass
        elif (
            not cmds.playbackOptions(q=True, max=True) == self.correct_end_frame
            or not cmds.playbackOptions(q=True, aet=True) == self.correct_end_frame
        ):
            error_duration.append(
                [f"Shot doesn't end at frame {self.correct_end_frame}.", None]
            )

        if error_duration:
            self.add_error(
                f"Shot doesn't end at frame {self.correct_end_frame}",
                f"Shot doesn't end at frame {self.correct_end_frame}",
                error_duration,
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
    info = f"Checks the frames per second. For this project it should be {gwaio.plugin.dccs['maya']['attributes']['fps']}."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correct_fps = gwaio.plugin.dccs['maya']['attributes']['fps']

    def process(self, context: Context) -> None:
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
        self.hierarchy_config = gwaio.plugin.dccs["maya"]["hierarchy"]

        create_hierarchy_from_dict(self.hierarchy_config)
        assemblies_cfg = self.hierarchy_config
        for rn in cmds.ls(references=True):
            logger.debug(f"Working on RN {rn}")
            path = cmds.referenceQuery(rn, f=True)
            parents = list(return_asset_parent(Path(path).stem, assemblies_cfg))
            self.root_nodes = return_root_nodes_from_reference(rn)
            logger.debug(f"The current root nodes of the RN are: {self.root_nodes}")
            logger.debug(f"The parent of the assets should be {', '.join(parents)}")
            for n in self.root_nodes:
                logger.debug(f"Working on root node {n} from reference {rn}")
                if (
                    all(not n.startswith(p) for p in parents)
                    or cmds.listRelatives(n, p=True) is None
                ):
                    self.add_error(
                        "Bad asset hierarchy",
                        f"{n} parent should be {', '.join(parents)}",
                        [[n,n]],
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
    # TODO
    name = "Check referenced assets"
    info = "Checks that all referenced assets are correct."

    def process(self, context: Context) -> None:
        # self.assets = self.context["entity.Shot.assets"] or list()

        # string = self.config["layout_manager.asset_placeholder"]
        # camera_path = gwaio.plugin.dccs["maya"]["schema"]["camera_file"]

        # asset_files = set(
        #     Path(f) for f in yield_asset_paths(string, self.assets, self.config)
        # )

        maya_dependencies = (cmds.referenceQuery(r, f=True, wcn=True) for r in return_top_refs())
        # refs = {Path(f) for f in maya_dependencies}
        # self.missing = missing = [fspath(f) for f in asset_files - refs]

        # cam_file = Path(camera_path).name
        # self.bad_refs = [
        #     fspath(f) for f in refs - asset_files if cam_file not in str(f)
        # ]
        # if missing:
        #     self.add_error(
        #                 "Missing references",
        #                 f"{missing} missing reference",
        #                 [[missing,missing]],
        #             )
        logger.debug("Check not implemented yet")

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
        export_cam("|cam|cam_master:CAM_MASTER|cam_master:cam_master")