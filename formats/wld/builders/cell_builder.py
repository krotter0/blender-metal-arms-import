import bpy
import math
from ..reader import FVisCell_t, FVisPlane_t
from ....common import vec, axis_convert

_EPSILON = 0.0001

class _IntersectionVertexData:
    def __init__(self, pos, plane_indices):
        self.pos = pos
        self.plane_indices = plane_indices

def build(index: int, cell: FVisCell_t):
    name = f"cell_{index}"
    print(f"Building cell: {name}")
    print(f"Cell bounding planes: {len(cell.bounding_planes)}")
    for i, plane in enumerate(cell.bounding_planes):
        print(f"  Plane {i}: normal={plane.normal}, point={plane.point}")

    verticies_info, plane_intersection_indices = _collect_intersections(cell)
    verticies = [axis_convert.to_blender_pos(vertex_data.pos) for vertex_data in verticies_info]

    for i, vertex in enumerate(verticies):
        print(f"Vertex {i}: pos={vertex}, planes={verticies_info[i].plane_indices}")
    faces = _build_faces(verticies_info, plane_intersection_indices, cell.bounding_planes)

    for i, face in enumerate(faces):
        print(f"Face {i}: verticies={face}")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    collection = bpy.context.collection
    collection.objects.link(obj)

    obj.hide_set(True)

    mesh.from_pydata(verticies, [], faces)
    mesh.update()

def _collect_intersections(cell: FVisCell_t):
    vertices_info = []
    plane_intersection_indices = [[] for _ in cell.bounding_planes]

    for i in range(len(cell.bounding_planes)):
        for j in range(i + 1, len(cell.bounding_planes)):
            for k in range(j + 1, len(cell.bounding_planes)):
                if i == j or j == k or i == k:
                    continue
                intersection = _plane_intersect(cell.bounding_planes[i], cell.bounding_planes[j], cell.bounding_planes[k])
                if intersection is not None and _is_vertex_inside(intersection, cell.bounding_planes):
                    vertex_index = None

                    if vertex_index is None:
                        vertex_index = len(vertices_info)
                        vertex_data = _IntersectionVertexData(intersection, (i, j, k))
                        vertices_info.append(vertex_data)

                    plane_intersection_indices[i].append(vertex_index)
                    plane_intersection_indices[j].append(vertex_index)
                    plane_intersection_indices[k].append(vertex_index)

    print(f"Intersections: {",".join([str(x.plane_indices) for x in vertices_info])}")
    print(f"Plane verticies: {",".join([str(x) for x in plane_intersection_indices])}")
    return vertices_info, plane_intersection_indices

def _is_vertex_inside(pos: tuple[float], planes: list[FVisPlane_t]):
    for plane in planes:
        if vec.dot(plane.normal, vec.sub(pos, plane.point)) < -_EPSILON:
            return False
    return True

def _build_faces(verticies_info: list[_IntersectionVertexData], plane_intersection_indices: list[list[int]], planes: list[FVisPlane_t]):
    faces = []
    for i, plane_indices in enumerate(plane_intersection_indices):
        face_vertex_indices = _build_face(verticies_info, plane_indices, planes[i])
        if face_vertex_indices is not None:
            print(f"Face for plane {i}: vertices={face_vertex_indices}")
            faces.append(face_vertex_indices)
    return faces

def _build_face(verticies_info: list[_IntersectionVertexData], plane_indices: list[int], plane: FVisPlane_t):
    if len(plane_indices) < 3:
        return None
    
    up_dir = (0, 1, 0)
    if abs(vec.dot(plane.normal, up_dir)) > 0.99:
        up_dir = (1, 0, 0)
    plane_dir_up = vec.cross(plane.normal, up_dir)
    plane_dir_side = vec.cross(plane.normal, plane_dir_up)
    
    projected_verticies = {}
    center = (0.0, 0.0)
    for vertex_index in plane_indices:
        vertex = verticies_info[vertex_index]
        u = vec.dot(vertex.pos, plane_dir_side)
        v = vec.dot(vertex.pos, plane_dir_up)
        projected_verticies[vertex_index] = (u, v)
        center = (center[0] + u, center[1] + v)
    center = (center[0] / len(plane_indices), center[1] / len(plane_indices))
    
    face_indices = []

    for vertex_index in plane_indices:
        (u, v) = projected_verticies[vertex_index]
        
        angle = -math.atan2(v - center[1], u - center[0])
        face_indices.append((vertex_index, angle))

    face_indices.sort(key=lambda x: x[1])
    return [index for index, _ in face_indices]

def _plane_intersect(a: FVisPlane_t, b: FVisPlane_t, c: FVisPlane_t):
    cross_a = vec.cross(b.normal, c.normal)
    cross_b = vec.cross(c.normal, a.normal)
    cross_c = vec.cross(a.normal, b.normal)

    determinant = vec.dot(a.normal, cross_a)

    if abs(determinant) < _EPSILON:
        return None
    
    determinant_inv = 1.0 / determinant
    
    d_a = -vec.dot(a.normal, a.point)
    d_b = -vec.dot(b.normal, b.point)
    d_c = -vec.dot(c.normal, c.point)
    
    return vec.mul(vec.add(
        vec.mul(cross_a, -d_a),
        vec.mul(cross_b, -d_b),
        vec.mul(cross_c, -d_c)
    ), determinant_inv)