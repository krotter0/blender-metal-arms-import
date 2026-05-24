import math

from ..types.world import FVisCell_t, FVisData_t, FVisPlane_t
from .models.cells import ParsedCell, ParsedVisCellFace
from dataclasses import dataclass
from ....common import vec, axis_convert

_EPSILON = 0.0001

class CellParser:
    @dataclass
    class _IntersectionVertexData:
        pos: tuple[float, float, float]
        plane_indices: list[int]

    def parse(self, cell: FVisCell_t, index: int | None = None) -> ParsedCell:
        planes = []
        if cell.bounding_planes is not None:
            planes = [cell.bounding_planes[i] for i in range(cell.plane_count)]

        vertices_info, plane_intersection_indices = CellParser._collect_intersections(cell)
        vertices = [axis_convert.to_blender_pos(vertex_data.pos) for vertex_data in vertices_info]
        faces = CellParser._build_faces(vertices_info, plane_intersection_indices, planes)

        return ParsedCell(
            index=index,
            parent_volume_idx=cell.parent_volume_idx,
            bounding_planes=planes,
            vertices=vertices,
            plane_faces=faces,
        )
    
    @staticmethod
    def _collect_intersections(cell: FVisCell_t):
        vertices_info = []
        plane_intersection_indices = [[] for _ in cell.bounding_planes]

        for i in range(len(cell.bounding_planes)):
            for j in range(i + 1, len(cell.bounding_planes)):
                for k in range(j + 1, len(cell.bounding_planes)):
                    intersection = CellParser._plane_intersect(cell.bounding_planes[i], cell.bounding_planes[j], cell.bounding_planes[k])
                    if intersection is not None and CellParser._is_vertex_inside(intersection, cell.bounding_planes):
                        vertex_index = None

                        if vertex_index is None:
                            vertex_index = len(vertices_info)
                            vertex_data = CellParser._IntersectionVertexData(intersection, (i, j, k))
                            vertices_info.append(vertex_data)

                        plane_intersection_indices[i].append(vertex_index)
                        plane_intersection_indices[j].append(vertex_index)
                        plane_intersection_indices[k].append(vertex_index)

        return vertices_info, plane_intersection_indices

    @staticmethod
    def _is_vertex_inside(pos: tuple[float, float, float], planes: list[FVisPlane_t]):
        for plane in planes:
            if vec.dot(plane.normal, vec.sub(pos, plane.point)) < -_EPSILON:
                return False
        return True

    @staticmethod
    def _build_faces(vertices_info: list[_IntersectionVertexData], plane_intersection_indices: list[list[int]], planes: list[FVisPlane_t]):
        faces = []
        for i, plane_indices in enumerate(plane_intersection_indices):
            face_vertex_indices = CellParser._build_face(vertices_info, plane_indices, planes[i])
            faces.append(face_vertex_indices)
        return faces

    @staticmethod
    def _build_face(vertices_info: list[_IntersectionVertexData], plane_indices: list[int], plane: FVisPlane_t) -> list[int] | None:
        if len(plane_indices) < 3:
            return None
        
        up_dir = (0, 1, 0)
        if abs(vec.dot(plane.normal, up_dir)) > 0.99:
            up_dir = (1, 0, 0)
        plane_dir_up = vec.cross(plane.normal, up_dir)
        plane_dir_side = vec.cross(plane.normal, plane_dir_up)
        
        projected_vertices = {}
        center = (0.0, 0.0)
        for vertex_index in plane_indices:
            vertex = vertices_info[vertex_index]
            u = vec.dot(vertex.pos, plane_dir_side)
            v = vec.dot(vertex.pos, plane_dir_up)
            projected_vertices[vertex_index] = (u, v)
            center = (center[0] + u, center[1] + v)
        center = (center[0] / len(plane_indices), center[1] / len(plane_indices))
        
        face_indices = []

        for vertex_index in plane_indices:
            (u, v) = projected_vertices[vertex_index]
            
            angle = -math.atan2(v - center[1], u - center[0])
            face_indices.append((vertex_index, angle))

        face_indices.sort(key=lambda x: x[1])
        return [index for index, _ in face_indices]

    @staticmethod
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