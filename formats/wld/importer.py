import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator

from ...common.platform import Platform
from ..common.reader import BinaryReader
from .reader import World
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

    import_portals: BoolProperty(
        name="Import Portals",
        description="Import portals from the .wld file.",
        default=True
    )

    import_autoportals: BoolProperty(
        name="Import Autoportals",
        description="Import PASM generated portals from the .wld file.",
        default=True
    )

    load_external_meshes: BoolProperty(
        name="Load External Meshes",
        description="Load external .ape files referenced by the .wld file from the same directory. When this option is disabled or a mesh cannot be found, objects will be created as empties. Note: Import will be SLOWER!",
        default=True
    )

    def execute(self, context):
        return self._read_wld(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")
        row.enabled = False

        row = col.row()
        row.prop(self, "import_lights")

        row = col.row()
        row.prop(self, "import_worldshapes")

        row = col.row()
        row.prop(self, "import_cells")

        row = col.row()
        row.prop(self, "import_portals")
        
        row = col.row()
        row.prop(self, "import_autoportals")
        row.enabled = self.import_portals

        row = col.row()
        row.prop(self, "load_external_meshes")

    def _read_wld(self, context):
        with BinaryReader(self.filepath, False) as reader:
            wld = World()
            wld.read(reader)

        options = world_builder.WorldBuildOptions()
        options.platform = Platform.parse(self.platform)
        options.filepath = self.filepath
        options.import_lights = self.import_lights
        options.import_worldshapes = self.import_worldshapes
        options.import_cells = self.import_cells
        options.import_portals = self.import_portals
        options.import_autoportals = self.import_autoportals
        options.load_external_meshes = self.load_external_meshes

        world_builder.build(wld, options)

        return {'FINISHED'}