from maya import cmds # type: ignore

def init_generic():
    print('#######################################################')
    print('############## Project: Generic HIA pipeline ##############')
    print('#######################################################')
    from datetime import datetime
    from typing import TYPE_CHECKING
    from os import fspath
    from pathlib import Path
    import sys
    starting_date = datetime.now()
    from functools import partial
    import maya_publisher  # type: ignore
    import maya_procedures  # type: ignore
    import inspect
    import os

    if TYPE_CHECKING:
        import gwaio

    print('[gwaio] Importing tools...')
    base_path = Path(os.path.abspath(inspect.getfile(inspect.currentframe()))).parent.parent
    sl_path = fspath(base_path)+"/tools/studio_library/src"
    sys.path.append(sl_path)

    sys.path.append(fspath(base_path.parent.parent))
    from dept.layout.procedures import lyt_creation_procedure, lyt_preview_procedure
    from dept.layout import publisher

    publisher_builder_data = {
        "blocking": {
            maya_publisher.CollectTask,
            maya_publisher.CollectPreview,
            maya_publisher.CollectFile,
            maya_publisher.CollectDescription,
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
            maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
        },
        "model": {
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
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
            maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
        },
        "uvs": {
            maya_publisher.CollectTask,
            maya_publisher.CollectFile,
            maya_publisher.CollectMov,
            maya_publisher.CollectDescription,
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
            maya_publisher.CheckUnweldedVertex,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            maya_publisher.PushSG,
        },
        "layout": {
            maya_publisher.CollectTask,
            maya_publisher.CollectPreview,
            maya_publisher.CollectFile,
            maya_publisher.CollectDescription,
            maya_publisher.CheckRepeatedNameNodes,
            maya_publisher.CheckPastedNodes,
            maya_publisher.CheckUnknownNodes,
            maya_publisher.CheckUnknownPlugins,
            maya_publisher.CheckScriptNodes,
            maya_publisher.CheckMayaFileNamingConvention,
            maya_publisher.CheckEmptyTransforms,
            maya_publisher.CheckEmptyReferenceNodes,
            publisher.CheckAssetsNameSpaces,
            publisher.CheckAudioFile,
            publisher.CheckResolution,
            publisher.CheckStartFrame,
            publisher.CheckDuration,
            publisher.CheckUnusedReferences,
            publisher.CheckFPS,
            publisher.CheckAssetHierarchy,
            publisher.CheckReferencedAssets,
            maya_publisher.PushSG,
        },
    }


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
                        "2.- Generate outliner": partial(print,"todo: outline generate"),
                        "3.- Auto rig": partial(maya_procedures.create_groups_and_controller),
                        "4.- Save": partial(maya_procedures.create_groups_and_controller),
                        "5.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["blocking"]),
                    },
                    "Model": {
                        "1.- Export turntable":partial(new_menu.on_export_turntable_low),
                        "2.- Auto rig":partial(maya_procedures.create_groups_and_controller),
                        "3.- Save": partial(print,"todo: save"),
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["model"]),
                    },
                    "UVs": {
                        "1.- Assign checker mat":partial(print,"todo: Assign checker mat"),
                        "2.- Export turntable":partial(new_menu.on_export_turntable_low),
                        "3.- Clear checker mat":partial(print,"todo: Clear checker mat"),
                        "4.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["uvs"]),
                        "publish": partial(maya_publisher.main,gwaio),
                    },
                    "Shading": {
                        "publish": partial(maya_publisher.main,gwaio),
                    },
                    "Rigging": {
                        "publish": partial(maya_publisher.main,gwaio),
                    },
                },
                "Shots": {
                    "Layout": {
                        "1.- Create base": partial(lyt_creation_procedure,gwaio),
                        "2.- Create preview": {
                            "720p": partial(lyt_preview_procedure,gwaio,[1280,720]),
                            "1080p": partial(lyt_preview_procedure,gwaio,[1920,1080]),
                        },
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["layout"]),
                    },
                    "Blocking": {
                        "1.- todo": partial(print,"todo: generate"),
                        "2.- todo": partial(print,"todo: generate"),
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["blocking"]),
                    },
                    "Refine": {
                        "1.- todo": partial(print,"todo: generate"),
                        "2.- todo": partial(print,"todo: generate"),
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["blocking"]),
                    },
                    "Fixing": {
                        "1.- todo": partial(print,"todo: generate"),
                        "2.- todo": partial(print,"todo: generate"),
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["blocking"]),
                    },
                    "Bake": {
                        "1.- todo": partial(print,"todo: generate"),
                        "2.- todo": partial(print,"todo: generate"),
                        "3.- Publish": partial(maya_publisher.main,gwaio,publisher_builder_data["blocking"]),
                    },
                }
            }
            new_menu.create_gwaio_menu(menu_cfg,new_menu.gwaio_menu)
        except Exception as e:
            print(e)

    add_gwaio_menu()
    finishing_date = datetime.now();print(f'userSetup loading time was: {finishing_date-starting_date}')

    # except:
    #     error = traceback.format_exc()
    #     cmds.evalDeferred(f'print(r"[gwaio] error : {error}")')

cmds.evalDeferred("print('[gwaio generic project] starting')", lp=True)
cmds.evalDeferred("init_generic()", lp=True)
cmds.evalDeferred("print('[gwaio generic project] finish')", lp=True)