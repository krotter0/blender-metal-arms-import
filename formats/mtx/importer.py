import os
import logging
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

from .parsers.animation import AnimParser
from ...common.report_stopwatch import ReportStopwatch
from ...common.platform import Platform
from .types.anim import FAnim_t
from .builders import anim_builder

logger = logging.getLogger(__name__)

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

    first_frame: IntProperty(
        name="First Frame",
        description="Which frame the animation should start on",
        default=1,
    )

    def execute(self, context):
        platform = Platform.parse(self.platform)
        frame_rate = self.frame_rate if not self.fps_match_scene else context.scene.render.fps
        return self._read_mtx(context, self.filepath, platform, frame_rate, self.first_frame)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(self, "platform")

        row = col.row()
        row.prop(self, "fps_match_scene")

        row = col.row()
        row.active = not self.fps_match_scene
        row.prop(self, "frame_rate")

        row = col.row()
        row.prop(self, "first_frame")

    def invoke(self, context, event):
        valid, message = self._check_selection_validity(context)
        if not valid:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        return super().invoke(context, event)

    def _read_mtx(self, context, filepath: str, platform: Platform, frame_rate: int, first_frame: int):
        valid, message = self._check_selection_validity(context)
        if not valid:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}

        stopwatch = ReportStopwatch(self.filepath, self)
        stopwatch.start()
        parser = AnimParser()
        mtx = FAnim_t()
        parsed_anim = None
        with mtx.bind_to_file(self.filepath, big_endian=platform.is_big_endian(), tags=[platform]):
            try:
                parsed_anim = parser.parse(mtx)
            except Exception:
                logger.exception(
                    "Failed to parse .mtx file '%s' for selected platform '%s'",
                    self.filepath,
                    self.platform,
                )
                self.report({'ERROR'}, f"Failed to parse .mtx, possible platform mismatch. See console for details.")
                return {'CANCELLED'}
            
        basename = os.path.basename(filepath)
        name = os.path.splitext(basename)[0]
        anim_builder.build(parsed_anim, name, frame_rate, first_frame)
        stopwatch.report()

        return {'FINISHED'}

    def _check_selection_validity(self, context):
        obj = context.active_object
        if not obj:
            return False, "No active object selected."

        if obj.type != 'ARMATURE':
            return False, "Selected object is not an armature."

        return True, ""