from ..formats.common.types.common import CFMtx43, CFMtx43A
from mathutils import Matrix


def to_blender_pos(pos):
    return (pos[0], pos[2], pos[1])

def to_blender_rot(rot):
    return (-rot.a, rot.x, rot.z, rot.y)

def mtx43_to_blender_mtx(mtx: CFMtx43):
    return Matrix((
        (mtx.x.x, mtx.z.x, mtx.y.x, mtx.a.x),
        (mtx.x.z, mtx.z.z, mtx.y.z, mtx.a.z),
        (mtx.x.y, mtx.z.y, mtx.y.y, mtx.a.y),
        (0, 0, 0, 1),
    ))

def mtx43a_to_blender_mtx(mtx: CFMtx43A):
    return Matrix((
        (mtx.x.x, mtx.z.x, mtx.y.x, mtx.a.x),
        (mtx.x.z, mtx.z.z, mtx.y.z, mtx.a.z),
        (mtx.x.y, mtx.z.y, mtx.y.y, mtx.a.y),
        (mtx.x.a, mtx.z.a, mtx.y.a, mtx.a.a),
    ))