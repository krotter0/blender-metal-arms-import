import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

from ..common import Platform
from ..reader.common import BinaryReader
from ..reader.ape import Ape
from .. import model_builder

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
            #("GC", "GameCube", ""),
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

    def execute(self, context):
        platform = Platform.parse(self.platform)

        lod_index = int(self.lod_index)
        if lod_index == -1:
            lod_index = None
        return self._read_ape(context, self.filepath, platform, lod_index, self.create_armature)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")
        row.enabled = False

        row = col.row()
        row.prop(self, "lod_index")

        row = col.row()
        row.prop(self, "create_armature")

    def _read_ape(self, context, filepath: str, platform: Platform, lod_index: int = None, create_armature: bool = True):
        with BinaryReader(filepath, False) as reader:
            ape = Ape()
            ape.read(reader)

            model_builder.create_ma_mesh(ape, lod_index, create_armature)

        return {'FINISHED'}