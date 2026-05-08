import bpy
import math
from ....formats.ape.reader import Ape
from mathutils import Quaternion, Vector
from ...common.reader import CFMtx43

from ..reader import CFWorldShapeBox, CFWorldShapeCylinder, CFWorldShapeInit, CFWorldShapeLine, CFWorldShapeMesh, CFWorldShapeSphere, CFWorldShapeSpline, LightType, World, WorldShapeType
from ....common import axis_convert
from ....formats.ape.builders import model_builder

class _WorldShapeBuildContext:
    def __init__(self, meshes: dict[str, Ape]):
        self.meshes = meshes

def build(index: int, worldshape: CFWorldShapeInit, meshes: dict[str, Ape]):
    _SHAPE_TYPE_TO_BUILDER_MAP = {
        WorldShapeType.POINT: _build_shape_point,
        WorldShapeType.LINE: _build_shape_line,
        WorldShapeType.SPLINE: _build_shape_spline,
        WorldShapeType.BOX: _build_shape_box,
        WorldShapeType.SPHERE: _build_shape_sphere,
        WorldShapeType.CYLINDER: _build_shape_cylinder,
        WorldShapeType.MESH: _build_shape_mesh,
    }

    context = _WorldShapeBuildContext(meshes)

    builder = _SHAPE_TYPE_TO_BUILDER_MAP.get(worldshape.type)
    if builder:
        obj = builder(index, worldshape, worldshape.shape, context)
        if obj is not None:
            _apply_gamedata_to_object(obj, worldshape)
        return obj
    else:
        print(f"Unsupported shape type: {worldshape.type}")
        return None

def _try_get_name(shape: CFWorldShapeInit, default_name: str = None):
    if shape.game_data == None:
        return default_name
    name_field = shape.game_data.get_first_table_by_key("name")
    if name_field == None or len(name_field.fields) == 0:
        return default_name
    return str(name_field.fields[0].value)

def _set_blender_obj_transform(obj: bpy.types.Object, mtx: CFMtx43):
    blender_mtx = axis_convert.mtx43_to_blender_mtx(mtx)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = blender_mtx.to_quaternion()
    obj.location = blender_mtx.to_translation()

def _to_local_points(points: list[tuple[float, float, float]], mtx: CFMtx43):
    inv_mtx = axis_convert.mtx43_to_blender_mtx(mtx).inverted_safe()
    return [tuple(inv_mtx @ Vector(point)) for point in points]

def _build_shape_point(index: int, init: CFWorldShapeInit, shape: None, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Point_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = 2.5

    _set_blender_obj_transform(obj, init.mtx)

    return obj

def _build_shape_box(index: int, init: CFWorldShapeInit, shape: CFWorldShapeBox, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Box_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'CUBE'
    obj.empty_display_size = 0.5

    _set_blender_obj_transform(obj, init.mtx)

    obj.scale = (shape.dim_x, shape.dim_z, shape.dim_y)
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_sphere(index: int, init: CFWorldShapeInit, shape: CFWorldShapeSphere, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Sphere_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = shape.radius

    _set_blender_obj_transform(obj, init.mtx)
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_line(index: int, init: CFWorldShapeInit, shape: CFWorldShapeLine, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Line_{index}")
    points = [(0, 0, 0), (0, shape.length, 0)]

    curve = _create_curve(name)
    obj = bpy.data.objects.new(name, curve)
    _set_blender_obj_transform(obj, init.mtx)
    _add_curve_spline(curve, points, 1.0, False)
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_spline(index: int, init: CFWorldShapeInit, shape: CFWorldShapeSpline, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Spline_{index}")
    points = [axis_convert.to_blender_pos(point) for point in shape.points]
    local_points = _to_local_points(points, init.mtx)
    
    curve = _create_curve(name)
    obj = bpy.data.objects.new(name, curve)
    _add_curve_spline(curve, local_points, 1.0, shape.closed)
    _set_blender_obj_transform(obj, init.mtx)
    bpy.context.collection.objects.link(obj)
    
    return obj

def _build_shape_cylinder(index: int, init: CFWorldShapeInit, shape: CFWorldShapeCylinder, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"Cylinder_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'CONE'
    obj.empty_display_size = 0.5

    obj.scale = (shape.radius, shape.dim_y, shape.radius)

    _set_blender_obj_transform(obj, init.mtx)
    obj.rotation_quaternion = obj.rotation_quaternion @ Quaternion((1.0, 0.0, 0.0), math.radians(-90.0))
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_mesh(index: int, init: CFWorldShapeInit, shape: CFWorldShapeMesh, context: _WorldShapeBuildContext):
    name = "obj_" + shape.mesh_name

    obj = None
    if context.meshes is None or shape.mesh_name not in context.meshes:
        obj = bpy.data.objects.new(name, None)

        obj.empty_display_type = 'ARROWS'
        obj.empty_display_size = 2.5
        bpy.context.collection.objects.link(obj)
    else:
        ape = context.meshes[shape.mesh_name]
        options = model_builder.ModelBuildOptions()
        options.create_armature = False
        options.merge_clusters = True
        options.name = name
        options.lod_index = 0
        obj = model_builder.build(ape, options)

    if obj is not None:
        _set_blender_obj_transform(obj, init.mtx)

    return obj

def _create_curve(name: str):
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'

    return curve

def _add_curve_spline(curve, points: list[tuple[float, float, float]], radius: float, cyclic: bool):
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, point in enumerate(points):
        spline.points[i].co = (*point, 1)
        spline.points[i].radius = radius
    spline.use_cyclic_u = cyclic
    return spline

def _apply_gamedata_to_object(obj: bpy.types.Object, init: CFWorldShapeInit):
    if init.game_data is None:
        return
    
    gamedata_strs = []
    for table in init.game_data.tables:
        values_str = ",".join([str(field) for field in table.fields])
        table_str = f"{table.name}={values_str}"
        gamedata_strs.append(table_str)

    gamedata_str = "\r\n".join(gamedata_strs)

    obj["ma"] = gamedata_str