from dataclasses import dataclass

@dataclass
class ParsedVisPlane:
    normal: tuple[float, float, float]
    point: tuple[float, float, float]

@dataclass
class ParsedVisCellFace:
    plane_index: int
    vertex_indices: list[int]

@dataclass
class ParsedCell:
    parent_volume_idx: int
    bounding_planes: list[ParsedVisPlane]
    plane_faces: list[list[int]]
    vertices: list[tuple[float, float, float]]
    index: int | None = None