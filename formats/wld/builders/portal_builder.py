import bpy
from mathutils import Vector
from ..parsers.models.portals import ParsedVisPortal

def build(portal: ParsedVisPortal):
    name = f"port_{portal.portal_id}"
    
    curve = bpy.data.curves.new(name, type='CURVE')
    obj = bpy.data.objects.new(name, curve)
    
    spline = curve.splines.new('POLY')
    spline.points.add(len(portal.vertices) - 1)

    center = Vector(portal.origin)
    for i, point in enumerate(portal.vertices):
        vertex = Vector(point)
        point_pos = vertex - center
        spline.points[i].co = (*point_pos, 1)
    spline.use_cyclic_u = True
    bpy.context.collection.objects.link(obj)
    obj.location = center
    return obj