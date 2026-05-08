import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

from ...common.platform import Platform
from .reader import Mtx
from ..common.reader import BinaryReader
from .builders import anim_builder

class ImportMtx(Operator, ImportHelper):
    """Import a Metal Arms Compiled Animation (.mtx) file"""
    bl_idname = "import_ma.mtx"
    bl_label = "Import .mtx"

    filename_ext = ".mtx"

    filter_glob: StringProperty(
        default="*.mtx",
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

    fps_match_scene: BoolProperty(
        name="Match frame rate to scene",
        description="Match the animation FPS to the scene FPS",
        default=True
    )

    frame_rate: IntProperty(
        name="Frame Rate",
        description="Frame rate to use for the animation (if not matching scene FPS)",
        default=30,
        min=1,
    )

    def execute(self, context):
        platform = Platform.parse(self.platform)
        frame_rate = self.frame_rate if not self.fps_match_scene else context.scene.render.fps
        return self._read_mtx(context, self.filepath, platform, frame_rate)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")

        row = col.row()

        row.prop(self, "fps_match_scene")

        row = layout.row()
        row.active = not self.fps_match_scene
        row.prop(self, "frame_rate")

    def invoke(self, context, event):
        valid, message = self._check_selection_validity(context)
        if not valid:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        return super().invoke(context, event)

    def _read_mtx(self, context, filepath: str, platform: Platform, frame_rate: int):
        valid, message = self._check_selection_validity(context)
        if not valid:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}

        with BinaryReader(filepath, platform.is_big_endian()) as reader:
            mtx = Mtx()
            mtx.read(reader)
            
            basename = os.path.basename(filepath)
            name = os.path.splitext(basename)[0]
            anim_builder.create_action(mtx, name, frame_rate)

        return {'FINISHED'}

    def _check_selection_validity(self, context):
        obj = context.active_object
        if not obj:
            return False, "No active object selected."

        if obj.type != 'ARMATURE':
            return False, "Selected object is not an armature."

        return True, ""