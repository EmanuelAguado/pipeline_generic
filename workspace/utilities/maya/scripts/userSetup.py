from maya import cmds  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import gwaio # type: ignore


def init_generic():
    print("[gwaio generic project] #######################################################")
    print("[gwaio generic project] ############## Project: Generic HIA pipeline ##########")
    print("[gwaio generic project] #######################################################")
    import os
    import inspect
    from datetime import datetime
    from os import fspath
    from pathlib import Path
    import sys
    from functools import partial

    import maya_publisher  # type: ignore
    import maya_procedures  # type: ignore
    import maya_utils  # type: ignore
    import maya_tools  # type: ignore

    starting_date = datetime.now()
    print("[gwaio generic project] Importing tools...")
    base_path = Path(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    ).parent.parent
    tools_path = fspath(base_path) + "/tools"
    sl_path = fspath(tools_path) + "/studio_library/src"
    sys.path.append(tools_path)
    sys.path.append(sl_path)

    sys.path.append(fspath(base_path.parent.parent))
    from dept.layout.procedures import (
        lyt_creation_procedure,
        lyt_export_camera_procedure,
        lyt_preview_procedure,
        lyt_import_camera_procedure,
        lyt_clean_camera_procedure,
    )
    from dept.anim.procedures import anim_creation_procedure, anim_preview_procedure
    from dept.layout import publisher as lyt_publisher
    from dept.anim import publisher as anim_publisher

    publisher_builder_data = {
        "modelblocking": [
            maya_publisher.CollectTask,
            maya_publisher.CollectPreview,
            maya_publisher.CollectFile,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckIntermediateShapes,
            maya_publisher.CheckNotConnectedGroupID,
            maya_publisher.CheckEnviromentVariables,
            maya_publisher.CheckUnusedShadingNodes,
            maya_publisher.CheckImagePlanes,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMeshesWhichHaveAnimation,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckUnusedAnimCurves,
            # maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "model": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckIntermediateShapes,
            maya_publisher.CheckNotConnectedGroupID,
            maya_publisher.CheckEnviromentVariables,
            maya_publisher.CheckUnusedShadingNodes,
            maya_publisher.CheckImagePlanes,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMeshesWhichHaveAnimation,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckUnusedAnimCurves,
            # maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "uvs": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckIntermediateShapes,
            maya_publisher.CheckNotConnectedGroupID,
            maya_publisher.CheckEnviromentVariables,
            maya_publisher.CheckUnusedShadingNodes,
            maya_publisher.CheckImagePlanes,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMeshesWhichHaveAnimation,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckUnusedAnimCurves,
            # maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "shading": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckIntermediateShapes,
            maya_publisher.CheckNotConnectedGroupID,
            maya_publisher.CheckEnviromentVariables,
            maya_publisher.CheckUnusedShadingNodes,
            maya_publisher.CheckImagePlanes,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMeshesWhichHaveAnimation,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckUnusedAnimCurves,
            # maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "rigging": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectPreview,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            # maya_publisher.CheckRepeatedNameNodes,
            # maya_publisher.CheckPastedNodes,
            # maya_publisher.CheckIntermediateShapes,
            # maya_publisher.CheckNotConnectedGroupID,
            # maya_publisher.CheckEnviromentVariables,
            # maya_publisher.CheckUnusedShadingNodes,
            # maya_publisher.CheckImagePlanes,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMeshesWhichHaveAnimation,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckUnusedAnimCurves,
            # maya_publisher.CheckUnweldedVertex,
            # maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "layout": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            # maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckUnknownNodes,
            # maya_publisher.CheckUnknownPlugins,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckEmptyReferenceNodes,
            lyt_publisher.CheckEmptyTransforms,
            lyt_publisher.CheckReferencedAssets,
            lyt_publisher.CheckUnusedReferences,
            lyt_publisher.CheckAssetsNameSpaces,
            lyt_publisher.CheckAssetHierarchy,
            lyt_publisher.CheckAudioFile,
            lyt_publisher.ExtractCamera,
            lyt_publisher.CheckResolution,
            lyt_publisher.CheckStartFrame,
            lyt_publisher.CheckDuration,
            lyt_publisher.CheckFPS,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "blocking": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            # maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckUnknownNodes,
            # maya_publisher.CheckUnknownPlugins,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckEmptyReferenceNodes,
            lyt_publisher.CheckEmptyTransforms,
            anim_publisher.CheckReferencedAssets,
            lyt_publisher.CheckUnusedReferences,
            lyt_publisher.CheckAssetsNameSpaces,
            lyt_publisher.CheckAssetHierarchy,
            lyt_publisher.CheckAudioFile,
            lyt_publisher.CheckResolution,
            lyt_publisher.CheckStartFrame,
            lyt_publisher.CheckDuration,
            lyt_publisher.CheckFPS,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "refine": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            # maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckUnknownNodes,
            # maya_publisher.CheckUnknownPlugins,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckEmptyReferenceNodes,
            lyt_publisher.CheckEmptyTransforms,
            anim_publisher.CheckReferencedAssets,
            lyt_publisher.CheckUnusedReferences,
            lyt_publisher.CheckAssetsNameSpaces,
            lyt_publisher.CheckAssetHierarchy,
            lyt_publisher.CheckAudioFile,
            lyt_publisher.CheckResolution,
            lyt_publisher.CheckStartFrame,
            lyt_publisher.CheckDuration,
            lyt_publisher.CheckFPS,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "fix": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            # maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckUnknownNodes,
            # maya_publisher.CheckUnknownPlugins,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckEmptyReferenceNodes,
            lyt_publisher.CheckEmptyTransforms,
            anim_publisher.CheckReferencedAssets,
            lyt_publisher.CheckUnusedReferences,
            lyt_publisher.CheckAssetsNameSpaces,
            lyt_publisher.CheckAssetHierarchy,
            lyt_publisher.CheckAudioFile,
            lyt_publisher.CheckResolution,
            lyt_publisher.CheckStartFrame,
            lyt_publisher.CheckDuration,
            lyt_publisher.CheckFPS,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
        "bake": [
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
            maya_publisher.CollectTimelog,
            maya_publisher.PushSG,
            maya_publisher.PushTimelog,
        ],
    }

    def on_layout_from_shot_generator(menu_cams):
        from pathlib import Path
        from re import compile
        from pipe_utils import return_highest_file  # type: ignore

        menu_cams.clear()
        version_regex = compile(gwaio.plugin.schema["version_regex"])
        folder_lyt_path = gwaio.plugin.work_to_publish(gwaio.task.serialize())[1]
        for lyt_w_folder, shot_name in list([f,f.stem] for f in Path(folder_lyt_path).parent.parent.glob("*")):
            lyt_p_folder = return_highest_file(version_regex,lyt_w_folder/"layout", ".ma")
            if not lyt_p_folder:
                continue
            print(f"Adding shot {shot_name} to layout creation menu")
            menu_cams.addAction(shot_name, partial(lyt_creation_procedure, gwaio, lyt_p_folder.as_posix()))

    # añadir los check desde la libreria de publisher y no la de utilities.maya
    def add_gwaio_menu():
        """You need to wrap the method around a partial call"""

        try:
            new_menu = gwaio.menu
            task = gwaio.task
            menu_cfg = {
                "Assets": {
                    "Blocking": {
                        "1.- Import reference": partial(maya_procedures.import_obj),
                        "2.- Generate outliner": partial(
                            print, "todo: outline generate"
                        ),
                        "3.- Auto rig": partial(
                            maya_procedures.create_groups_and_controller
                        ),
                        "4.- Save": partial(
                            maya_procedures.create_groups_and_controller
                        ),
                        "5.- Publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["modelblocking"],
                        ),
                    },
                    "Model": {
                        "1.- Export turntable": partial(
                            new_menu.on_export_turntable_low
                        ),
                        "2.- Auto rig": partial(
                            maya_procedures.create_groups_and_controller
                        ),
                        "3.- Save": partial(print, "todo: save"),
                        "3.- Publish": partial(
                            maya_publisher.main, gwaio, publisher_builder_data["model"]
                        ),
                    },
                    "UVs": {
                        "1.- Assign checker mat": partial(
                            print, "todo: Assign checker mat"
                        ),
                        "2.- Export turntable": partial(
                            new_menu.on_export_turntable_low
                        ),
                        "3.- Clear checker mat": partial(
                            print, "todo: Clear checker mat"
                        ),
                        "4.- Publish": partial(
                            maya_publisher.main, gwaio, publisher_builder_data["uvs"]
                        ),
                        "publish": partial(maya_publisher.main, gwaio),
                    },
                    "Shading": {
                        "publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["shading"],
                        ),
                    },
                    "Rigging": {
                        "publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["rigging"],
                        ),
                    },
                },
                "Shots": {
                    "Layout": {
                        "1.- Create base": {
                            "Master key": partial(lyt_creation_procedure, gwaio),
                            "From shots": ["auto_menu", on_layout_from_shot_generator],
                        },
                        "2.- Asset management": partial(maya_tools.HiAssetManager().show),
                        "3.- Test Bake camera": {
                            "Export bake camera": partial(
                                lyt_export_camera_procedure, gwaio
                            ),
                            "Import bake camera": partial(
                                lyt_import_camera_procedure, gwaio
                            ),
                            "Clean bake camera": partial(
                                lyt_clean_camera_procedure, gwaio
                            ),
                        },
                        "4.- Create preview": {
                            "720p": partial(lyt_preview_procedure, gwaio, [1280, 720]),
                            "1080p": partial(
                                lyt_preview_procedure, gwaio, [1920, 1080]
                            ),
                        },
                        "5.- Publish": partial(
                            maya_publisher.main, gwaio, publisher_builder_data["layout"]
                        ),
                    },
                    "Blocking": {
                        "1.- Create base": partial(anim_creation_procedure, gwaio),
                        "2.- Create preview": {
                            "720p": partial(anim_preview_procedure, gwaio, [1280, 720]),
                            "1080p": partial(
                                anim_preview_procedure, gwaio, [1920, 1080]
                            ),
                        },
                        "3.- Publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["blocking"],
                        ),
                    },
                    "Refine": {
                        "1.- Create base": partial(anim_creation_procedure, gwaio),
                        "2.- Create preview": {
                            "720p": partial(anim_preview_procedure, gwaio, [1280, 720]),
                            "1080p": partial(
                                anim_preview_procedure, gwaio, [1920, 1080]
                            ),
                        },
                        "3.- Publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["refine"],
                        ),
                    },
                    "Fixing": {
                        "1.- Create base": partial(anim_creation_procedure, gwaio),
                        "2.- Create preview": {
                            "720p": partial(anim_preview_procedure, gwaio, [1280, 720]),
                            "1080p": partial(
                                anim_preview_procedure, gwaio, [1920, 1080]
                            ),
                        },
                        "3.- Publish": partial(
                            maya_publisher.main,
                            gwaio,
                            publisher_builder_data["fix"],
                        ),
                    },
                    "Bake": {
                        "1.- todo": partial(print, "todo: generate"),
                        "2.- todo": partial(print, "todo: generate"),
                        "3.- Publish": partial(
                            maya_publisher.main, gwaio, publisher_builder_data["bake"]
                        ),
                    },
                },
            }
            new_menu.create_gwaio_menu(menu_cfg, new_menu.gwaio_menu)
        except Exception as e:
            print(e)

    add_gwaio_menu()
    finishing_date = datetime.now()
    print(f"userSetup loading time was: {finishing_date-starting_date}")

    # except:
    #     error = traceback.format_exc()
    #     cmds.evalDeferred(f'print(r"[gwaio] error : {error}")')


cmds.evalDeferred("print('[gwaio generic project] starting')", lp=True)
cmds.evalDeferred("init_generic()", lp=True)
cmds.evalDeferred("print('[gwaio generic project] finish')", lp=True)
