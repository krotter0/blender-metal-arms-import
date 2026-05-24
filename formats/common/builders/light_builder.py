import bpy
import math

from ..parsers.models.light import ParsedLight

from ..types.common import CFColorRGB
from ....common import axis_convert
from mathutils import Quaternion, Color, Matrix

from ..types.light import LightType

def build(index: int, parsed_light: ParsedLight) -> bpy.types.Object | None:
    _LIGHT_TYPE_TO_BUILDER_MAP = {
        LightType.DIRECTIONAL: _build_light_directional,
        LightType.OMNIDIRECTIONAL: _build_light_omnidirectional,
        LightType.SPOT: _build_light_spot,
    }
    builder = _LIGHT_TYPE_TO_BUILDER_MAP.get(parsed_light.type)
    if builder:
        obj = builder(index, parsed_light)
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            _set_common_light_properties(obj, obj.data, parsed_light)
        return obj
    else:
        print(f"Unsupported light type: {parsed_light.type}")

def build_ambient(color: tuple[float, float, float], intensity: float):
    obj = _build_light_ambient(color, intensity)
    if obj is not None:
        bpy.context.collection.objects.link(obj)

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

def _set_common_light_properties(obj, light: bpy.types.Light, parsed_light: ParsedLight):
    color = Color((parsed_light.motif_color[0] * 255, parsed_light.motif_color[1] * 255, parsed_light.motif_color[2] * 255))
    light.color = color.from_srgb_to_scene_linear()
    light.energy = parsed_light.intensity
    light.shadow_soft_size = parsed_light.radius

    obj.data["ma_light_props"] = {
        "fIntensity": parsed_light.intensity,
        "fRadius": parsed_light.radius,
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

def _build_light_ambient(color: tuple[float, float, float], intensity: float):
    name = "ambient"
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