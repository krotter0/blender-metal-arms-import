from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from ...common.property_groups.texture_import_settings import TextureImportSettings

from ...common.platform import Platform
from ...common.binary_reader import BinaryReader
from .types.model import Ape
from .builders import model_builder

class ImportApe(Operator, ImportHelper):
    """Import a Metal Arms Compiled Mesh (.ape) file"""
    bl_idname = "import_ma.ape"
    bl_label = "Import .ape"

    filename_ext = ".ape"

    filter_glob: StringProperty(
        default="*.ape",
        options={'HIDDEN'},
        maxlen=255,
    )

    platform: EnumProperty(
        name="Platform",
        items=[
            ("DX", "Xbox", ""),
            ("GC", "GameCube", ""),
        ],
        default="DX"
    )

    lod_index: EnumProperty(
        name="LODs to import",
        description="Limits import to meshes of a specific Level of Detail.",
        items=[
            ('-1', "All LODs", ""),
            ('0', "LOD 0", ""),
            ('1', "LOD 1", ""),
            ('2', "LOD 2", ""),
            ('3', "LOD 3", ""),
            ('4', "LOD 4", ""),
            ('5', "LOD 5", ""),
            ('6', "LOD 6", ""),
            ('7', "LOD 7", ""),
        ],
        default='-1',
    )

    create_armature: BoolProperty(
        name="Create Armature",
        description="Create an armature for the imported mesh",
        default=True
    )

    merge_clusters: BoolProperty(
        name="Merge Clusters",
        description="Import .ape as a single Blender object",
        default=False
    )

    def execute(self, context):
        if not context.window_manager.ma_texture_import_settings.is_valid():
            self.report({'ERROR'}, "Invalid texture folder path.")
            return {'CANCELLED'}
        return self._read_ape(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")

        row = col.row()
        row.prop(self, "lod_index")

        row = col.row()
        row.prop(self, "create_armature")

        row = col.row()
        row.prop(self, "merge_clusters")

        context.window_manager.ma_texture_import_settings.draw(context, layout)

    def _read_ape(self, context):
        platform = Platform.parse(self.platform)
        with BinaryReader(self.filepath, platform.is_big_endian()) as reader:
            ape = Ape(platform)
            ape.read(reader)
            
            lod_index = int(self.lod_index)
            if lod_index == -1:
                lod_index = None

            options = model_builder.ModelBuildOptions()
            options.platform = platform
            options.filepath = self.filepath
            options.lod_index = lod_index
            options.create_armature = self.create_armature
            options.merge_clusters = self.merge_clusters
            options.texture_folder_path = context.window_manager.ma_texture_import_settings.get_path()
            options.texture_allow_recurse = context.window_manager.ma_texture_import_settings.texture_allow_recurse

            model_builder.build(ape, options)

        return {'FINISHED'}