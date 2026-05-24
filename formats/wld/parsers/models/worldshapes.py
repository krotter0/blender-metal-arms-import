from dataclasses import dataclass

from ...types.world import WorldShapeType
from ....csv.parsers.models.csv import ParsedCSV

@dataclass
class ParsedWorldShapeLine:
    length: float

@dataclass
class ParsedWorldShapeSpline:
    closed: bool
    points: list

@dataclass
class ParsedWorldShapeBox:
    size: tuple[float, float, float]

@dataclass
class ParsedWorldShapeSphere:
    radius: float

@dataclass
class ParsedWorldShapeCylinder:
    radius: float
    length: float

@dataclass
class ParsedWorldShapeMesh:
    mesh_name: str

@dataclass
class ParsedWorldShapeInit:
    type: WorldShapeType
    shape: None | ParsedWorldShapeLine | ParsedWorldShapeSpline | ParsedWorldShapeBox | ParsedWorldShapeSphere | ParsedWorldShapeCylinder | ParsedWorldShapeMesh
    mtx: tuple[tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float]]
    parent_shape_index: int
    game_data: ParsedCSV | None