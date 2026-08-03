from enum import Flag

from ....common.platform import Platform

from .model_dx import FDX8MeshMaterial_t, FDX8MeshMaterial_t_Beta, FDX8Mesh_t
from .model_gc import FGCMeshMaterial_t, FGCMesh_t
from .skeleton import *
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from ...common.types.light import *
from .texture import *

class MtlFlags(Flag):
    NONE = 0x0000
    NOCOLLIDE = 0x0001
    RENDER_LAST = 0x0002
    ZWRITE_ON = 0x0004
    DO_NOT_TINT = 0x0008
    DO_NOT_CAST_SHADOWS = 0x0010
    INVERT_EMISSIVE_MASK = 0x0020
    ANGULAR_EMISSIVE = 0x0040
    ANGULAR_TRANSLUCENCY = 0x0080
    NO_ALPHA_SCROLL = 0x0100

class FMeshSeg_t(Struct):
    bound_sphere_ms: CFSphere = Field(CFSphere)
    bone_mtx_count: int = Field(u8)
    bone_mtx_indices: list[int] = ArrayOf(u8, 4)
    Padding(3)

class FMeshMaterial_t(Struct):
    light_registers: Pointer[None] = VoidPointerField()
    surface_registers: Pointer[None] = VoidPointerField()

    light_shader_idx: int = Field(u8)
    specular_shader_idx: int = Field(u8)
    surface_shader_idx: int = Field(u16)

    part_id_mask: int = Field(u32)
    BeginUnion()
    platform_data_dx: Pointer[FDX8MeshMaterial_t] = RequiresTag(Platform.DX, PointerTo(FDX8MeshMaterial_t))
    platform_data_gc: Pointer[FGCMeshMaterial_t] = RequiresTag(Platform.GC, PointerTo(FGCMeshMaterial_t))
    EndUnion()

    lod_mask: int = Field(u8)
    depth_bias_level: int = Field(u8)
    base_st_sets: int = Field(u8)
    lightmap_st_sets: int = Field(u8)
    tex_layer_id_index: list[int] = ArrayOf(u8, 4)
    affect_angle: float = Field(f32)
    affect_normal: list[float] = ArrayOf(s8, 3)
    affect_bone_id: int = Field(s8)
    compressed_radius: int = Field(u8)
    Padding(1)
    mtl_flags: MtlFlags = Field(EnumType(MtlFlags, 2))
    draw_key: int = Field(u32)
    material_tint: CFColorRGB = Field(CFColorRGB)
    average_vert_pos: CFVec3 = Field(CFVec3)
    hash_key: int = Field(u32)
    
class FMeshMaterial_t_Beta(Struct):
    light_registers: Pointer[None] = VoidPointerField()
    surface_registers: Pointer[None] = VoidPointerField()

    light_shader_idx: int = Field(u8)
    specular_shader_idx: int = Field(u8)
    surface_shader_idx: int = Field(u16)

    part_id_mask: int = Field(u32)
    BeginUnion()
    platform_data_dx: Pointer[FDX8MeshMaterial_t_Beta] = RequiresTag(Platform.DX_BETA, PointerTo(FDX8MeshMaterial_t_Beta))
    EndUnion()

    lod_mask: int = Field(u8)
    depth_bias_level: int = Field(u8)
    base_st_sets: int = Field(u8)
    lightmap_st_sets: int = Field(u8)
    tex_layer_id_index: list[int] = ArrayOf(u8, 4)
    affect_angle: float = Field(f32)
    affect_normal: list[float] = ArrayOf(s8, 3)
    affect_bone_id: int = Field(s8)
    compressed_radius: int = Field(u8)
    Padding(1)
    mtl_flags: MtlFlags = Field(EnumType(MtlFlags, 2))
    material_tint: CFColorRGB = Field(CFColorRGB)
    average_vert_pos: CFVec3 = Field(CFVec3)
    hash_key: int = Field(u32)

class FMesh_t(Struct):
    name: str = Field(FixedSizeString(16))
    bound_sphere_ms: CFSphere = Field(CFSphere)
    bound_box_min_ms: CFVec3 = Field(CFVec3)
    bound_box_max_ms: CFVec3 = Field(CFVec3)
    flags: int = Field(u16)
    mesh_coll_mask: int = Field(u16)
    used_bone_count: int = Field(u8)
    root_bone_index: int = Field(u8)
    bone_count: int = Field(u8)
    seg_count: int = Field(u8)
    tex_layer_id_count: int = Field(u8)
    tex_layer_id_count_st: int = Field(u8)
    tex_layer_id_count_flip: int = Field(u8)
    light_count: int = Field(u8)
    material_count: int = Field(u8)
    coll_tree_count: int = Field(u8)
    lod_count: int = Field(u8)
    shadow_lod_bias: int = Field(u8)
    lod_distances: list[float] = ArrayOf(f32, 8)
    segs: IterablePointer[FMeshSeg_t] = PointerToIterable(FMeshSeg_t, 'seg_count')
    
    BeginUnion()
    bones_dx: IterablePointer[FMeshBone_t_DX] = PointerToIterable(FMeshBone_t_DX, 'bone_count')
    bones_gc: IterablePointer[FMeshBone_t] = PointerToIterable(FMeshBone_t, 'bone_count')
    EndUnion()
    
    lights: IterablePointer[FLightInit_t] = PointerToIterable(FLightInit_t, 'light_count')
    skeleton_index_array: Pointer[int] = PointerTo(u8)
    BeginUnion()
    materials: IterablePointer[FMeshMaterial_t] = PointerToIterable(FMeshMaterial_t, 'material_count')
    materials_beta: IterablePointer[FMeshMaterial_t_Beta] = PointerToIterable(FMeshMaterial_t_Beta, 'material_count')
    EndUnion()
    coll_trees = Skip(4)
    tex_layer_id_array: IterablePointer[FMeshTexLayerID_t] = PointerToIterable(FMeshTexLayerID_t, 'tex_layer_id_count')
    
    BeginUnion()
    mesh_is_dx: Pointer[FDX8Mesh_t] = RequiresEitherTag([Platform.DX, Platform.DX_BETA], PointerTo(FDX8Mesh_t))
    mesh_is_gc: Pointer[FGCMesh_t] = RequiresTag(Platform.GC, PointerTo(FGCMesh_t))
    EndUnion()