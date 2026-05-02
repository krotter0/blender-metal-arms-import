
def to_blender_pos(pos):
    return (pos.x, pos.z, pos.y)

def to_blender_rot(rot):
    return (-rot.a, rot.x, rot.z, rot.y)