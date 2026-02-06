from pathlib import Path
from typing import TYPE_CHECKING

from GENERIC.pipeline.workspace.utilities.maya.scripts.maya_tools import AssetManager
from maya_procedures import (  # type: ignore
    import_file,
    reference_file,
    reference_replace,
    return_asset_parent,
)

if TYPE_CHECKING:
    import gwaio  # type: ignore

hierarchy_config = gwaio.plugin.dccs["maya"]["hierarchy"]

class HiAssetManager(AssetManager):
    def on_import_file(self, file_path):
        return import_file(file_path)

    def on_reference_file(self, file_path, namespace):
        asset_ns = Path(file_path).stem + "_rn0"
        parent = next(return_asset_parent(Path(file_path).stem, hierarchy_config), None)
        return reference_file(file_path, asset_ns, parent)

    def on_replace_file(self, file_path, reference, namespace):
        asset_ns = Path(file_path).stem + "_rn0"
        parent = next(return_asset_parent(Path(file_path).stem, hierarchy_config), None)
        return reference_replace(
            file_path,
            reference,
            asset_ns,
        )  