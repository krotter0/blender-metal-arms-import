import bpy
import math
from mathutils import Quaternion, Vector, Matrix

from ..parsers.models.worldshapes import *
from ..types.world import WorldShapeType
from ....formats.ape.builders import model_builder
from ...ape.parsers.models.model import ParsedModel
from ....common.star_command_assembler import StarCommandAssembler

class _WorldShapeBuildContext:
    def __init__(self, precomputed_meshes: dict[str, ParsedModel]):
        self.external_models = precomputed_meshes

def build(index: int, worldshape: ParsedWorldShapeInit, precomputed_meshes: dict[str, ParsedModel], star_commands: list[str] = None):
    _SHAPE_TYPE_TO_BUILDER_MAP = {
        WorldShapeType.POINT: _build_shape_point,
        WorldShapeType.LINE: _build_shape_line,
        WorldShapeType.SPLINE: _build_shape_spline,
        WorldShapeType.BOX: _build_shape_box,
        WorldShapeType.SPHERE: _build_shape_sphere,
        WorldShapeType.CYLINDER: _build_shape_cylinder,
        WorldShapeType.MESH: _build_shape_mesh,
    }

    context = _WorldShapeBuildContext(precomputed_meshes)

    builder = _SHAPE_TYPE_TO_BUILDER_MAP.get(worldshape.type)
    if builder:
        obj = builder(index, worldshape, worldshape.shape, context)
        if obj is not None:
            _apply_gamedata_to_object(obj, worldshape)
            _apply_star_commands(obj, star_commands)
        return obj
    else:
        print(f"Unsupported shape type: {worldshape.type}")
        return None

def _try_get_name(shape: ParsedWorldShapeInit, default_name: str = None):
    if shape.game_data == None:
        return default_name
    name_table = shape.game_data.get_first_table_by_key("name")
    if name_table == None or len(name_table) == 0:
        return default_name
    return name_table[0]

def _set_blender_obj_transform(obj: bpy.types.Object, mtx: tuple):
    blender_mtx = Matrix(mtx)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = blender_mtx.to_quaternion()
    obj.location = blender_mtx.to_translation()
    obj.scale = blender_mtx.to_scale()

def _to_local_points(points: list[tuple[float, float, float]], mtx: tuple):
    inv_mtx = Matrix(mtx).inverted_safe()
    return [tuple(inv_mtx @ Vector(point)) for point in points]

def _build_shape_point(index: int, init: ParsedWorldShapeInit, shape: None, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"point_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = 2.5

    _set_blender_obj_transform(obj, init.mtx)

    return obj

def _build_shape_box(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeBox, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"box_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'CUBE'
    obj.empty_display_size = 0.5

    _set_blender_obj_transform(obj, init.mtx)

    obj.scale = shape.size
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_sphere(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeSphere, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"sphere_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = shape.radius

    _set_blender_obj_transform(obj, init.mtx)
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_line(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeLine, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"line_{index}")
    points = [(0, 0, 0), (0, shape.length, 0)]

    curve = _create_curve(name)
    obj = bpy.data.objects.new(name, curve)
    _set_blender_obj_transform(obj, init.mtx)
    _add_curve_spline(curve, points, 1.0, False)
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_spline(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeSpline, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"spline_{index}")
    points = [Vector(point) for point in shape.points]
    local_points = _to_local_points(points, init.mtx)
    
    curve = _create_curve(name)
    obj = bpy.data.objects.new(name, curve)
    _add_curve_spline(curve, local_points, 1.0, shape.closed)
    _set_blender_obj_transform(obj, init.mtx)
    bpy.context.collection.objects.link(obj)
    
    return obj

def _build_shape_cylinder(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeCylinder, context: _WorldShapeBuildContext):
    name = _try_get_name(init, f"cylinder_{index}")
    obj = bpy.data.objects.new(name, None)

    obj.empty_display_type = 'CONE'
    obj.empty_display_size = 0.5

    obj.scale = (shape.radius, shape.length, shape.radius)

    _set_blender_obj_transform(obj, init.mtx)
    obj.rotation_quaternion = obj.rotation_quaternion @ Quaternion((1.0, 0.0, 0.0), math.radians(-90.0))
    bpy.context.collection.objects.link(obj)

    return obj

def _build_shape_mesh(index: int, init: ParsedWorldShapeInit, shape: ParsedWorldShapeMesh, context: _WorldShapeBuildContext):
    name = "obj_" + shape.mesh_name

    obj = None
    if context.external_models is None or shape.mesh_name not in context.external_models:
        obj = bpy.data.objects.new(name, None)

        obj.empty_display_type = 'ARROWS'
        obj.empty_display_size = 2.5
        bpy.context.collection.objects.link(obj)
    else:
        model = context.external_models[shape.mesh_name]
        options = model_builder.ModelBuildOptions()
        options.create_armature = False
        options.import_lights = False
        options.merge_clusters = True
        options.name = name
        options.lod_index = 0
        options.apply_lod_name_prefix = False
        _, objs = model_builder.build(model, options)
        if objs is not None and len(objs) > 0:
            obj = objs[0]

    if obj is not None:
        _set_blender_obj_transform(obj, init.mtx)

    return obj

def _apply_star_commands(obj: bpy.types.Object, star_commands: list[str] = None):
    # (added by lightmap recovery, e.g. *nolmuse; also kept as a property, as names stop at 63 characters)
    if not star_commands:
        return
    suffix = StarCommandAssembler(list(star_commands)).assemble()
    obj.name = obj.name + suffix
    obj["ma_lightmap"] = {"star_commands": suffix}

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

def _apply_gamedata_to_object(obj: bpy.types.Object, init: ParsedWorldShapeInit):
    if init.game_data is None:
        return
    
    gamedata_strs = []
    for table_name, tables in init.game_data.tables.items():
        for table in tables:
            values_str = ",".join([str(field) for field in table])
            table_str = f"{table_name}={values_str}"
            gamedata_strs.append(table_str)

    gamedata_str = "\r\n".join(gamedata_strs)

    obj["ma"] = gamedata_str