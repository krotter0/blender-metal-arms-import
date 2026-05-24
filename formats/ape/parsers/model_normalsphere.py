import math

_NORMAL_SPHERE_NORMAL_NULL = 0
_NORMAL_SPHERE_NORMAL_UP = 32768
_NORMAL_SPHERE_NORMAL_DOWN = 32769
_NORMAL_SPHERE_NORMAL_RIGHT = 32770
_NORMAL_SPHERE_NORMAL_LEFT = 32771
_NORMAL_SPHERE_NORMAL_FORWARD = 32772
_NORMAL_SPHERE_NORMAL_BACKWARD = 32773
_NORMAL_SPHERE_OCT_OFFSET = 4096
_NORMAL_SPHERE_MAX_INDEX = 32800

def _calculate_normal_sphere():
    normals: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * _NORMAL_SPHERE_MAX_INDEX
    normals[_NORMAL_SPHERE_NORMAL_NULL] = (0.0, 0.0, 0.0)
    normals[_NORMAL_SPHERE_NORMAL_UP] = (0.0, 1.0, 0.0)
    normals[_NORMAL_SPHERE_NORMAL_DOWN] = (0.0, -1.0, 0.0)
    normals[_NORMAL_SPHERE_NORMAL_RIGHT] = (1.0, 0.0, 0.0)
    normals[_NORMAL_SPHERE_NORMAL_LEFT] = (-1.0, 0.0, 0.0)
    normals[_NORMAL_SPHERE_NORMAL_FORWARD] = (0.0, 0.0, 1.0)
    normals[_NORMAL_SPHERE_NORMAL_BACKWARD] = (0.0, 0.0, -1.0)

    index = 1
    angle = 1
    for angle in range(1, 91):
        rad_angle = math.radians(angle)
        y = math.cos(rad_angle)
        
        slice_radius = math.sin(rad_angle)
        increment = 90 / angle
        for slice in range(angle, 0, -1):
            rad_slice = math.radians(slice * increment)
            x = slice_radius * math.sin(rad_slice)
            z = slice_radius * math.cos(rad_slice)

            normals[index] = (x, y, z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET] = (-x, y, z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 2] = (-x, y, -z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 3] = (x, y, -z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 4] = (x, -y, z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 5] = (-x, -y, z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 6] = (-x, -y, -z)
            normals[index + _NORMAL_SPHERE_OCT_OFFSET * 7] = (x, -y, -z)

            index += 1

    return normals

NORMAL_SPHERE = _calculate_normal_sphere()