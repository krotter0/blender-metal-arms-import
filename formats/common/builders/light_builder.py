import bpy
import math

from ..parsers.models.light import ParsedLight

from ..types.common import CFColorRGB
from ....common import axis_convert
from mathutils import Quaternion, Color, Matrix

from ..types.light import LightType
from ....common.star_command_assembler import StarCommandAssembler

def build(index: int, parsed_light: ParsedLight, collection: bpy.types.Collection = None) -> bpy.types.Object | None:
    if parsed_light.skip:
        return None
    _LIGHT_TYPE_TO_BUILDER_MAP = {
        LightType.DIRECTIONAL: _build_light_directional,
        LightType.OMNIDIRECTIONAL: _build_light_omnidirectional,
        LightType.SPOT: _build_light_spot,
    }
    builder = _LIGHT_TYPE_TO_BUILDER_MAP.get(parsed_light.type)
    if builder:
        obj = builder(index, parsed_light)
        if obj is not None:
            (collection or bpy.context.collection).objects.link(obj)
            set_light_values(obj, parsed_light.motif_color, parsed_light.intensity, parsed_light.radius)
            apply_star_commands_and_props(obj, parsed_light.extra_star_commands, parsed_light.extra_props)
        return obj
    else:
        print(f"Unsupported light type: {parsed_light.type}")

def build_ambient(color: tuple[float, float, float], intensity: float, name: str = "ambient", star_commands: list[str] = None, extra_props: dict = None, collection: bpy.types.Collection = None):
    obj = _build_light_ambient(color, intensity, name)
    if obj is not None:
        (collection or bpy.context.collection).objects.link(obj)
        apply_star_commands_and_props(obj, star_commands, extra_props)
    return obj

def apply_star_commands_and_props(obj: bpy.types.Object, star_commands: list[str] = None, extra_props: dict = None):
    """Appends star commands to the object's name (and its light's) and stores extra properties as ma_lightmap."""
    if star_commands:
        suffix = StarCommandAssembler(list(star_commands)).assemble()
        obj.name = obj.name + suffix
        if obj.data is not None:
            obj.data.name = obj.data.name + suffix
    if extra_props:
        obj["ma_lightmap"] = extra_props

def _try_get_name(parsed_light: ParsedLight, default_name: str = None):
    if parsed_light.name is not None and parsed_light.name != "":
        # Strip star commands
        split = parsed_light.name.split("*")
        return split[0]
    
    return default_name

def _set_blender_obj_transform(obj, parsed_light: ParsedLight):
    orientation_mtx = Matrix(parsed_light.mtx_orientation)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = orientation_mtx.to_quaternion()
    obj.location = parsed_light.pos

def set_light_values(obj, color: tuple, intensity: float, radius: float):
    light: bpy.types.Light = obj.data
    color = Color((color[0] * 255, color[1] * 255, color[2] * 255))
    light.color = color.from_srgb_to_scene_linear()
    light.energy = intensity
    light.shadow_soft_size = radius

    obj.data["ma_light_props"] = {
        "fIntensity": intensity,
        "fRadius": radius,
    }

def _build_light_omnidirectional(index: int, parsed_light: ParsedLight):
    name = _try_get_name(parsed_light, f"omnilight_{index}")
    light = bpy.data.lights.new(name, type='POINT')
    obj = bpy.data.objects.new(name, light)

    _set_blender_obj_transform(obj, parsed_light)

    return obj

def _build_light_directional(index: int, parsed_light: ParsedLight):
    name = _try_get_name(parsed_light, f"directionallight_{index}")
    light = bpy.data.lights.new(name, type='SUN')
    obj = bpy.data.objects.new(name, light)

    _set_blender_obj_transform(obj, parsed_light)

    return obj

def _build_light_spot(index: int, parsed_light: ParsedLight):
    name = _try_get_name(parsed_light, f"spotlight_{index}")
    light = bpy.data.lights.new(name, type='SPOT')
    obj = bpy.data.objects.new(name, light)
    
    light.spot_size = parsed_light.spot_outer_radians
    light.spot_blend = -((parsed_light.spot_inner_radians / light.spot_size) - 1)

    _set_blender_obj_transform(obj, parsed_light)
    obj.rotation_quaternion = obj.rotation_quaternion @ Quaternion((1.0, 0.0, 0.0), math.radians(90.0))

    return obj

def _build_light_ambient(color: tuple[float, float, float], intensity: float, name: str = "ambient"):
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = 2.5

    game_data = {
        "red": color[0],
        "green": color[1],
        "blue": color[2],
        "intensity": intensity,
    }

    game_data_str = "\r\n".join([f"{key}={value}" for key, value in game_data.items()])

    obj["ma"] = game_data_str

    return obj