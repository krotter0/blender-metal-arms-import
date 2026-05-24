from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from enum import Flag

class BoneFlags(Flag):
    NONE = 0x00
    VOIDBONE = 0x01
    SKINNEDBONE = 0x02

class FMeshSkeleton_t(Struct):
    parent_bone_index: int = Field(u8)
    child_bone_count: int = Field(u8)
    child_array_start_index: int = Field(u8)

class FMeshBone_t(Struct):
    name: str = Field(FixedSizeString(32))
    at_rest_bone_to_model_mtx: CFMtx43A = Field(CFMtx43A)
    at_rest_model_to_bone_mtx: CFMtx43A = Field(CFMtx43A)
    at_rest_parent_to_bone_mtx: CFMtx43A = Field(CFMtx43A)
    at_rest_bone_to_parent_mtx: CFMtx43A = Field(CFMtx43A)
    segmented_bound_sphere_bs: CFSphere = Field(CFSphere)
    skeleton: FMeshSkeleton_t = Field(FMeshSkeleton_t)
    flags: BoneFlags = Field(EnumType(BoneFlags, 1))
    part_id: int = Field(u8)
    Padding(3)

class FMeshBone_t_DX(FMeshBone_t):
    Padding(8)