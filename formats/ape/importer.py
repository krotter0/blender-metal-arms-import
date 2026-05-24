import logging
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .parsers.model_gc import ModelParserGC
from .parsers.model_dx import ModelParserDX
from ...structs.field import *
from ...structs.fieldtype import *
from ...structs.structs import *
from ...structs.virtualmemory import *
from ...common.report_stopwatch import ReportStopwatch
from ...common.platform import Platform
from .types.model import FMesh_t
from .builders import model_builder

logger = logging.getLogger(__name__)

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

    hide_lods: BoolProperty(
        name="Hide LODs",
        description="Hide lower LOD meshes after import.",
        default=True
    )

    create_armature: BoolProperty(
        name="Create Armature",
        description="Create an armature for the imported mesh",
        default=True
    )

    merge_clusters: BoolProperty(
        name="Merge Meshes",
        description="Merge model segments into a single Blender object (still separated by LOD).",
        default=True
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
        row.enabled = self.lod_index == '-1'
        row.prop(self, "hide_lods")

        row = col.row()
        row.prop(self, "create_armature")

        row = col.row()
        row.prop(self, "merge_clusters")

        context.window_manager.ma_texture_import_settings.draw(context, layout)

    def _read_ape(self, context):
        stopwatch = ReportStopwatch(self.filepath, self)
        stopwatch.start()
        platform = Platform.parse(self.platform)

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
        options.texture_extension = context.window_manager.ma_texture_import_settings.texture_extension

        parser = ModelParserDX() if platform == Platform.DX else ModelParserGC()
        ape = FMesh_t()
        parsed_model = None
        with ape.bind_to_file(self.filepath, big_endian=platform.is_big_endian(), tags=[platform]):
            try:
                lod_filter = {options.lod_index} if options.lod_index is not None else None
                parsed_model = parser.parse(ape, lod_filter)
            except Exception:
                logger.exception(
                    "Failed to parse .ape file '%s' for selected platform '%s'",
                    self.filepath,
                    self.platform,
                )
                self.report({'ERROR'}, f"Failed to parse .ape, possible platform mismatch. See console for details.")
                return {'CANCELLED'}
        model_builder.build(parsed_model, options)
        stopwatch.report()

        return {'FINISHED'}