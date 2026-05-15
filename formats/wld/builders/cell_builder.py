import bpy
import math
from ..types.world import FVisCell_t, FVisData_t, FVisPlane_t
from ....common import vec, axis_convert

_EPSILON = 0.0001

class _IntersectionVertexData:
    def __init__(self, pos, plane_indices):
        self.pos = pos
        self.plane_indices = plane_indices

def build_with_volumes(vis: FVisData_t, skip_first_cell: bool = False):
    volumes = vis.volumes
    if skip_first_cell and len(volumes) > 0:
        volumes = volumes[1:]

    for volume in volumes:
        collection = bpy.context.collection
        if volume.cell_count > 1:
            volume_collection = bpy.data.collections.new(f"cell_volume_{volume.volume_id}")
            collection.children.link(volume_collection)
            collection = volume_collection
            
        for cell_index in range(volume.cell_first_idx, volume.cell_first_idx + volume.cell_count):
            cell = vis.cells[cell_index]
            build(cell_index, cell, collection)

def build(index: int, cell: FVisCell_t, parent_collection: bpy.types.Collection = None):
    parent_collection = parent_collection or bpy.context.collection

    name = f"cell_{index}"

    verticies_info, plane_intersection_indices = _collect_intersections(cell)
    verticies = [axis_convert.to_blender_pos(vertex_data.pos) for vertex_data in verticies_info]

    faces = _build_faces(verticies_info, plane_intersection_indices, cell.bounding_planes)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    parent_collection.objects.link(obj)

    obj.hide_set(True)

    mesh.from_pydata(verticies, [], faces)
    mesh.update()

def _collect_intersections(cell: FVisCell_t):
    vertices_info = []
    plane_intersection_indices = [[] for _ in cell.bounding_planes]

    for i in range(len(cell.bounding_planes)):
        for j in range(i + 1, len(cell.bounding_planes)):
            for k in range(j + 1, len(cell.bounding_planes)):
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