import bpy
from ....common import axis_convert, vec
from ..reader import FVisPortal_t, PortalFlags

def build(portal: FVisPortal_t, skip_if_autoportal=True):
    if skip_if_autoportal and portal.flags & PortalFlags.AUTO_PORTAL:
        return None
    
    name = f"port_{portal.portal_id}"
    
    curve = bpy.data.curves.new(name, type='CURVE')
    obj = bpy.data.objects.new(name, curve)
    
    spline = curve.splines.new('POLY')
    spline.points.add(len(portal.verticies) - 1)

    converted_center = axis_convert.to_blender_pos(portal.bounding_sphere_ws.pos)
    for i, point in enumerate(portal.verticies):
        converted_point = axis_convert.to_blender_pos(point)
        point_pos = vec.sub(converted_point, converted_center)
        spline.points[i].co = (*point_pos, 1)
    spline.use_cyclic_u = True
    bpy.context.collection.objects.link(obj)
    obj.location = converted_center
    return obj