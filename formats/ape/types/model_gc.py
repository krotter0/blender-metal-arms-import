from .skeleton import *
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from ...common.types.light import *
from .texture import *

class GCVertexPositionType(Enum):
    U8 = 0
    S8 = 1
    U16 = 2
    S16 = 3
    F32 = 4

class GCVertexAttributeType(Enum):
    NONE = 0
    DIRECT = 1
    INDEX8 = 2
    INDEX16 = 3

class GCVertexFormat(Enum):
    VTXFMT0 = 0
    VTXFMT1 = 1
    VTXFMT2 = 2
    VTXFMT3 = 3
    VTXFMT4 = 4
    VTXFMT5 = 5
    VTXFMT6 = 6
    VARIABLE_VTXFMT = 7

class GCVBFlags(Flag):
    NONE = 0x00
    SKINNED = 0x01
    NORM_NBT = 0x10

class GCDLContFlags(Flag):
    NONE = 0x00
    SKINNED = 0x01
    CONSTANT_COLOR = 0x02
    BUMPMAP = 0x04
    FACING_OPP_DIR_LIGHT = 0x08
    STREAMING = 0x80

class FGCColor_t(Struct):
    r: int = Field(u8)
    g: int = Field(u8)
    b: int = Field(u8)
    a: int = Field(u8)

class FGCST16_t(Struct):
    s: int = Field(u16)
    t: int = Field(u16)

class FGCNBT8_t(Struct):
    nx: int = Field(s8)
    ny: int = Field(s8)
    nz: int = Field(s8)

    bx: int = Field(s8)
    by: int = Field(s8)
    bz: int = Field(s8)
    
    tx: int = Field(s8)
    ty: int = Field(s8)
    tz: int = Field(s8)

class FGCMeshSkin_t(Struct):
    trans_desc_count: int = Field(u16)
    td1mtx_count: int = Field(u16)
    td2mtx_count: int = Field(u16)
    td3or4mtx_count: int = Field(u16)
    trans_desc: int = Field(u32)
    skinned_verts_count: int = Field(u32)
    skinned_verts: int = Field(u32)
    skin_weights: int = Field(u32)

class FGCVB_t(Struct):
    flags: GCVBFlags = Field(EnumType(GCVBFlags, 2))
    pos_count: int = Field(u16)
    pos_type: GCVertexPositionType = Field(EnumType(GCVertexPositionType, 1))
    pos_idx_type: GCVertexAttributeType = Field(EnumType(GCVertexAttributeType, 1))
    pos_stride: int = Field(u8)
    pos_frac: int = Field(u8)
    diffuse_count: int = Field(u16)
    color_idx_type: GCVertexAttributeType = Field(EnumType(GCVertexAttributeType, 1))
    gc_vertex_format: GCVertexFormat = Field(EnumType(GCVertexFormat, 1))
    positions: Pointer[None] = VoidPointer()
    diffuse: Pointer[FGCColor_t] = PointerToIterable(FGCColor_t, 'diffuse_count')
    sts: Pointer[FGCST16_t] = PointerTo(FGCST16_t)
    nbt: Pointer[FGCNBT8_t] = PointerTo(FGCNBT8_t)

class FGC_DLCont_t(Struct):
    flags: GCDLContFlags = Field(EnumType(GCDLContFlags, 1))
    matrix_idx: int = Field(u8)
    lod_id: int = Field(u8)
    part_id: int = Field(u8)
    strip_tri_count: int = Field(u16)
    list_tri_count: int = Field(u16)
    strip_count: int = Field(u16)
    list_count: int = Field(u8)
    vb_index: int = Field(u8)
    size: int = Field(u32)
    buffer: Pointer[None] = VoidPointer()
    constant_color: FGCColor_t = Field(FGCColor_t)

class FGCMeshMaterial_t(Struct):
    dl_container: IterablePointer[FGC_DLCont_t] = IterablePointerField(FGC_DLCont_t, 'dl_container_count')
    dl_container_count: int = Field(u16)

class FGCMesh_t(Struct):
    mesh: Pointer[None] = VoidPointer() #This is actually a FMesh_t ptr instead of a void ptr, that'd be a circular reference tho
    at_rest_bound_sphere_ms: CFSphere = Field(CFSphere)
    flags: int = Field(u8)
    vb_count: int = Field(u8)
    mtl_count: int = Field(u16)
    vb: Pointer[FGCVB_t] = PointerToIterable(FGCVB_t, 'vb_count')
    mesh_skin: Pointer[FGCMeshSkin_t] = PointerTo(FGCMeshSkin_t)