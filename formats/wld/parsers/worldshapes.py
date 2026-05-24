from ....structs.pointer import Pointer

from ...csv.types.csv import DataGameFileDataType, FDataGamFile_Header_t
from ..types.world import (
    CFWorldShapeBox,
    CFWorldShapeCylinder,
    CFWorldShapeInit,
    CFWorldShapeLine,
    CFWorldShapeMesh,
    CFWorldShapeSphere,
    CFWorldShapeSpline,
    FData_WorldFileHeader_t,
    FData_WorldInitHeader_t,
    WorldShapeType,
)
from .models.worldshapes import (
    ParsedWorldShapeInit,
    ParsedWorldShapeBox,
    ParsedWorldShapeCylinder,
    ParsedWorldShapeLine,
    ParsedWorldShapeMesh,
    ParsedWorldShapeSphere,
    ParsedWorldShapeSpline,
)
from ....formats.csv.parsers.csv import CSVParser

class WorldShapeParser:
    def __init__(self):
        self._csv_parser = CSVParser()

    def _parse_line(self, shape: CFWorldShapeLine):
        return ParsedWorldShapeLine(length=shape.length)
    
    def _parse_spline(self, shape: CFWorldShapeSpline):
        points = [(p[0], p[2], p[1]) for p in shape.points]
        return ParsedWorldShapeSpline(closed=shape.closed, points=points)
    
    def _parse_box(self, shape: CFWorldShapeBox):
        return ParsedWorldShapeBox(size=(shape.dim_x, shape.dim_z, shape.dim_y))
    
    def _parse_sphere(self, shape: CFWorldShapeSphere):
        return ParsedWorldShapeSphere(radius=shape.radius)
    
    def _parse_cylinder(self, shape: CFWorldShapeCylinder):
        return ParsedWorldShapeCylinder(radius=shape.radius, length=shape.dim_y)
    
    def _parse_mesh(self, shape: CFWorldShapeMesh):
        mesh_name = shape.mesh_name.deref
        return ParsedWorldShapeMesh(mesh_name=mesh_name)

    def _parse_shape(self, worldshape_init: CFWorldShapeInit):
        shape_type = worldshape_init.shape_type
        if shape_type == WorldShapeType.POINT:
            return None
        elif shape_type == WorldShapeType.LINE:
            return self._parse_line(worldshape_init.line.deref)
        elif shape_type == WorldShapeType.SPLINE:
            return self._parse_spline(worldshape_init.spline.deref)
        elif shape_type == WorldShapeType.BOX:
            return self._parse_box(worldshape_init.box.deref)
        elif shape_type == WorldShapeType.SPHERE:
            return self._parse_sphere(worldshape_init.sphere.deref)
        elif shape_type == WorldShapeType.CYLINDER:
            return self._parse_cylinder(worldshape_init.cylinder.deref)
        elif shape_type == WorldShapeType.MESH:
            return self._parse_mesh(worldshape_init.mesh.deref)
        else:
            raise ValueError(f"Unknown world shape type: {shape_type}")

    def parse(self, worldshape_init: CFWorldShapeInit):
        mtx = worldshape_init.mtx
        mtx = (
            (mtx[0][0], mtx[2][0], mtx[1][0], mtx[3][0]),
            (mtx[0][2], mtx[2][2], mtx[1][2], mtx[3][2]),
            (mtx[0][1], mtx[2][1], mtx[1][1], mtx[3][1]),
            (0.0, 0.0, 0.0, 1.0),
        )
        shape_type = worldshape_init.shape_type
        shape_data = self._parse_shape(worldshape_init)

        game_data = None
        if worldshape_init.game_data is not None and worldshape_init.game_data.address != 0:
            csv_memory = worldshape_init.memory.copy(worldshape_init.game_data.address)
            game_data_ptr = Pointer[FDataGamFile_Header_t](csv_memory, 0, FDataGamFile_Header_t)
            game_data = self._csv_parser.parse(game_data_ptr.deref)

        return ParsedWorldShapeInit(
            type=shape_type,
            shape=shape_data,
            mtx=mtx,
            parent_shape_index=worldshape_init.parent_shape_index,
            game_data=game_data,
        )