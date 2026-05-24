import bpy
import logging
from io import BytesIO
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator

from ...common.report_stopwatch import ReportStopwatch
from ...common.platform import Platform
from .types.world import FData_WorldFileHeader_t
from .parsers.world import WorldParser
from .builders import world_builder

logger = logging.getLogger(__name__)
        
class ImportWld(Operator, ImportHelper):
    """Import a Metal Arms Compiled World (.wld) file"""
    bl_idname = "import_ma.wld"
    bl_label = "Import .wld"

    filename_ext = ".wld"

    filter_glob: StringProperty(
        default="*.wld",
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

    import_meshes: BoolProperty(
        name="Import Meshes",
        description="Import world meshes (terrain) from the .wld file.",
        default=True
    )

    import_lights: BoolProperty(
        name="Import Lights",
        description="Import lights from the .wld file.",
        default=True
    )

    import_worldshapes: BoolProperty(
        name="Import Worldshapes",
        description="Import worldshapes from the .wld file.",
        default=True
    )

    import_cells: BoolProperty(
        name="Import Cells",
        description="Import cells from the .wld file.",
        default=True
    )

    skip_first_cell: BoolProperty(
        name="Skip First Cell",
        description="Skip the first cell in the .wld file. This is generally a generated cell that encompasses the entire world.",
        default=True
    )

    import_portals: BoolProperty(
        name="Import Portals",
        description="Import portals from the .wld file.",
        default=True
    )

    skip_autoportals: BoolProperty(
        name="Skip Autoportals",
        description="Skip PASM generated portals from the .wld file.",
        default=True
    )

    load_external_meshes: BoolProperty(
        name="Load External Meshes",
        description="Load external .ape files referenced by the .wld file from the same directory. When this option is disabled or a mesh cannot be found, objects will be created as empties. Note: Import will be SLOWER!",
        default=True
    )

    def execute(self, context):
        if not context.window_manager.ma_texture_import_settings.is_valid():
            self.report({'ERROR'}, "Invalid texture folder path.")
            return {'CANCELLED'}
        return self._read_wld(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")

        row = col.row()
        row.prop(self, "import_meshes")

        row = col.row()
        row.prop(self, "import_lights")

        row = col.row()
        row.prop(self, "import_worldshapes")

        row = col.row()
        row.prop(self, "import_cells")

        row = col.row()
        row.prop(self, "skip_first_cell")
        row.enabled = self.import_cells

        row = col.row()
        row.prop(self, "import_portals")
        
        row = col.row()
        row.prop(self, "skip_autoportals")
        row.enabled = self.import_portals

        row = col.row()
        row.prop(self, "load_external_meshes")
        
        context.window_manager.ma_texture_import_settings.draw(context, layout)

    def _read_wld(self, context):
        stopwatch = ReportStopwatch(self.filepath, self)
        stopwatch.start()
        platform = Platform.parse(self.platform)

        options = world_builder.WorldBuildOptions()
        options.platform = platform
        options.filepath = self.filepath
        options.import_meshes = self.import_meshes
        options.import_lights = self.import_lights
        options.import_worldshapes = self.import_worldshapes
        options.import_cells = self.import_cells
        options.import_portals = self.import_portals
        options.import_autoportals = not self.skip_autoportals
        options.skip_first_cell = self.skip_first_cell
        options.load_external_meshes = self.load_external_meshes
        options.texture_folder_path = context.window_manager.ma_texture_import_settings.get_path()
        options.texture_allow_recurse = context.window_manager.ma_texture_import_settings.texture_allow_recurse
        options.texture_extension = context.window_manager.ma_texture_import_settings.texture_extension

        world = FData_WorldFileHeader_t()
        parser = WorldParser(platform)
        parsed_world = None
        with world.bind_to_file(self.filepath, big_endian=platform.is_big_endian(), tags=[platform]):
            try:
                parsed_world = parser.parse(world)
            except Exception:
                logger.exception(
                    "Failed to parse .wld file '%s' for selected platform '%s'",
                    self.filepath,
                    self.platform,
                )
                self.report({'ERROR'}, f"Failed to parse .wld, possible platform mismatch. See console for details.")
                return {'CANCELLED'}
        world_builder.build(parsed_world, options)
        stopwatch.report()

        return {'FINISHED'}