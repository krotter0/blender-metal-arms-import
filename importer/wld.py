import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty
from bpy.types import Operator

from ..common import Platform
from ..reader.common import BinaryReader
from ..reader.wld import World
from .. import model_builder
        
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

    def execute(self, context):
        platform = Platform.parse(self.platform)
        return self._read_wld(context, self.filepath, platform)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")
        row.enabled = False

    def _read_wld(self, context, filepath: str, platform: Platform):
        with BinaryReader(filepath, False) as reader:
            wld = World()
            wld.read(reader)

            for mesh in wld.meshes:
                model_builder.create_ma_mesh(mesh)

        return {'FINISHED'}