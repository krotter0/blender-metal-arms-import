import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator

from ...common.platform import Platform
from ...common.binary_reader import BinaryReader
from .types.world import World
from .builders import world_builder
        
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
            #("GC", "GameCube", ""),
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
        row.enabled = False

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
        with BinaryReader(self.filepath, False) as reader:
            wld = World()
            wld.read(reader)

        options = world_builder.WorldBuildOptions()
        options.platform = Platform.parse(self.platform)
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

        world_builder.build(wld, options)

        return {'FINISHED'}