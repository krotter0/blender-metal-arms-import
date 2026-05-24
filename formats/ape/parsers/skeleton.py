from typing import Self

from .models.skeleton import ParsedSkeleton, ParsedBone
from ....structs.pointer import *

from ..types.model import FMesh_t
from ..types.skeleton import FMeshBone_t

class SkeletonParser:
    def __init__(self):
        self._parsed_skeleton: ParsedSkeleton = None

    def _parse_bones(self, bones: IterablePointer[FMeshBone_t]):
        parsed_bones: list[ParsedBone] = []
        for i, bone in enumerate(bones):
            name = bone.name
            parent_index = bone.skeleton.parent_bone_index
            mtx = bone.at_rest_bone_to_model_mtx
            bone_to_model_matrix = (
                (mtx.x.x, mtx.z.x, mtx.y.x, mtx.a.x),
                (mtx.x.z, mtx.z.z, mtx.y.z, mtx.a.z),
                (mtx.x.y, mtx.z.y, mtx.y.y, mtx.a.y),
                (mtx.x.a, mtx.z.a, mtx.y.a, mtx.a.a)
            )

            parsed_bone = ParsedBone(i, name, parent_index, bone_to_model_matrix)
            parsed_bones.append(parsed_bone)
        self._parsed_skeleton.bones = parsed_bones
    
    def _build_hierarchy(self, parsed_bones: list[ParsedBone]):
        root_bones = []
        for parsed_bone in parsed_bones:
            parent_index = parsed_bone.parent_index
            if parent_index == 255:
                root_bones.append(parsed_bone)
            else:
                parent_bone = parsed_bones[parent_index]
                parsed_bone.parent_bone = parent_bone
                parent_bone.children.append(parsed_bone)
        self._parsed_skeleton.root_bones = root_bones
    
    def _parse_platform_specific(self):
        raise NotImplementedError("Must be implemented by subclass")

    def parse(self, model: FMesh_t) -> ParsedSkeleton:
        skeleton = ParsedSkeleton()
        self._parsed_skeleton = skeleton
        self._model = model

        self._parse_platform_specific()
        self._build_hierarchy(skeleton.bones)

        self._parsed_skeleton = None
        self._model = None
        return skeleton