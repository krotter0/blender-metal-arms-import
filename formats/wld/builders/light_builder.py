import bpy
import math
from ....common import axis_convert
from mathutils import Quaternion, Color

from ..reader import FLightInit_t, FVisData_t, LightType

def build(index: int, lightinit: FLightInit_t):
    _LIGHT_TYPE_TO_BUILDER_MAP = {
        LightType.DIRECTIONAL: _build_light_directional,
        LightType.OMNIDIRECTIONAL: _build_light_omnidirectional,
        LightType.SPOT: _build_light_spot,
    }
    builder = _LIGHT_TYPE_TO_BUILDER_MAP.get(lightinit.type)
    if builder:
        obj = builder(index, lightinit)
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            _set_common_light_properties(obj, obj.data, lightinit)
    else:
        print(f"Unsupported light type: {lightinit.type}")

def build_ambient(vis: FVisData_t):
    obj = _build_light_ambient(vis)
    if obj is not None:
        bpy.context.collection.objects.link(obj)

def _set_blender_obj_transform(obj, lightinit: FLightInit_t):
    blender_mtx = axis_convert.mtx43_to_blender_mtx(lightinit.mtx_orientation)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = blender_mtx.to_quaternion()
    obj.location = axis_convert.to_blender_pos(lightinit.influence.pos)

def _set_common_light_properties(obj, light: bpy.types.Light, lightinit: FLightInit_t):
    color = Color((lightinit.motif.r * 255, lightinit.motif.g * 255, lightinit.motif.b * 255))
    light.color = color.from_srgb_to_scene_linear()
    light.energy = lightinit.intensity
    light.shadow_soft_size = lightinit.influence.radius

    obj.data["ma_light_props"] = {
        "fIntensity": lightinit.intensity,
        "fRadius": lightinit.influence.radius,
    }

def _build_light_omnidirectional(index: int, lightinit: FLightInit_t):
    name = f"OmniLight_{index}"
    light = bpy.data.lights.new(name, type='POINT')
    obj = bpy.data.objects.new(name, light)

    _set_blender_obj_transform(obj, lightinit)

    return obj

def _build_light_directional(index: int, lightinit: FLightInit_t):
    name = f"DirectionalLight_{index}"
    light = bpy.data.lights.new(name, type='SUN')
    obj = bpy.data.objects.new(name, light)

    _set_blender_obj_transform(obj, lightinit)

    return obj

def _build_light_spot(index: int, lightinit: FLightInit_t):
    name = f"SpotLight_{index}"
    light = bpy.data.lights.new(name, type='SPOT')
    obj = bpy.data.objects.new(name, light)
    
    light.spot_size = lightinit.spot_outer_radians
    light.spot_blend = -((lightinit.spot_inner_radians / light.spot_size) - 1)

    _set_blender_obj_transform(obj, lightinit)
    obj.rotation_quaternion = obj.rotation_quaternion @ Quaternion((1.0, 0.0, 0.0), math.radians(90.0))

    return obj

def _build_light_ambient(vis: FVisData_t):
    name = f"ambient"
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = 2.5

    game_data = {
        "red": vis.ambient_light_color.r,
        "green": vis.ambient_light_color.g,
        "blue": vis.ambient_light_color.b,
        "intensity": vis.ambient_light_intensity,
    }

    game_data_str = "\r\n".join([f"{key}={value}" for key, value in game_data.items()])

    obj["ma"] = game_data_str

    return obj