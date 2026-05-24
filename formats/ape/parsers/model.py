from collections.abc import Sequence
from typing import Self

from ...common.parsers.light import LightParser
from ....structs.pointer import Pointer

from .skeleton import SkeletonParser
from .material import MaterialParser
from ..types.model import FMesh_t
from .models.model import ParsedModel

class ModelParser:
    def __init__(self, skeleton_parser: SkeletonParser, material_parser: MaterialParser):
        self._parsed_model: ParsedModel = None
        self._lod_filter: set[int] = None
        self._skeleton_parser = skeleton_parser
        self._light_parser = LightParser()
        self._material_parser = material_parser
        self._streaming_pointer: Pointer[None] = None

    def _indices_to_triangle_list_faces(self, indices: Sequence[int], triangle_count: int, start_index: int = 0):
        end_index = start_index + triangle_count * 3
        return [(indices[i], indices[i + 1], indices[i + 2]) for i in range(start_index, end_index, 3)]

    def _indices_to_triangle_strip_faces(self, indices: Sequence[int], triangle_count: int, start_index: int = 0):
        faces = []
        for i in range(start_index, start_index + triangle_count):
            i0 = indices[i]
            i1 = indices[i + 1]
            i2 = indices[i + 2]

            if (i - start_index) % 2 == 0:
                face = (i0, i1, i2)
            else:
                face = (i1, i0, i2)

            if i0 != i1 and i1 != i2 and i0 != i2:
                faces.append(face)

        return faces

    def _parse(self):
        self._parsed_model.name = self._model.name

        self._parse_skeleton()
        self._parse_lights()
        self._parse_materials()
        self._parse_platform_specific()
    
    def _parse_platform_specific(self):
        raise NotImplementedError("Platform specific parse method not implemented for model parser")
    
    def _parse_skeleton(self):
        if self._model.bone_count > 0:
            skeleton = self._skeleton_parser.parse(self._model)
            self._parsed_model.skeleton = skeleton

    def _parse_lights(self):
        if self._model.light_count == 0:
            self._parsed_model.lights = []
        else:
            lights = [self._light_parser.parse(light) for light in self._model.lights]
            self._parsed_model.lights = lights

    def _parse_materials(self):
        if self._model.material_count == 0:
            self._parsed_model.materials = []
        else:
            materials = [self._material_parser.parse(mat, self._model) for mat in self._model.materials]
            self._parsed_model.materials = materials

    def parse(self, model: FMesh_t, lod_filter: set[int] = None, streaming_pointer: Pointer[None] = None):
        parsed_model = ParsedModel()

        self._parsed_model = parsed_model
        self._lod_filter = lod_filter
        self._model = model
        self._streaming_pointer = streaming_pointer

        self._parse()

        self._parsed_model = None
        self._lod_filter = None
        self._model = None
        self._streaming_pointer = None

        return parsed_model