from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from enum import Flag

class TexLayerIdFlags(Flag):
    NONE = 0x00
    USE_ST_INFO = 0x01
    USE_FLIP_INFO = 0x02
    BEGIN_SCROLLING = 0x04
    BEGIN_FLIPPING = 0x08
    BEGIN_ROTATING = 0x10

class FTexInfo_t(Struct):
    tex_name: str = Field(FixedSizeString(16))
    user_data: Pointer[None] = VoidPointer()
    tex_fmt: int = Field(u8)
    pal_fmt: int = Field(u8)
    flags: int = Field(u8)
    lod_count: int = Field(u8)
    render_target_stencil_bit_count: int = Field(u8)
    render_target_depth_bit_count: int = Field(u8)
    Padding(2)
    texels_across: int = Field(u16)
    texels_down: int = Field(u16)

class CFTexInst(Struct):
    Padding(0x18)

class FShTexInst_t(Struct):
    tex_inst: CFTexInst = Field(CFTexInst)
    texture_name_offset: int = Field(u16)
    tex_layer_id: int = Field(u8)
    Padding(1)

class FMeshTexLayerID_t(Struct):
    tex_layer_id: int = Field(u8)
    flags: TexLayerIdFlags = Field(EnumType(TexLayerIdFlags, 1))
    flip_page_count: int = Field(u8)
    frames_per_flip: int = Field(u8)
    flip_palette: Pointer[Pointer[CFTexInst]] = PointerTo(PointerTo(CFTexInst))
    scroll_st_per_sec: CFVec2 = Field(CFVec2)
    uv_degree_rotation_per_sec: float = Field(f32)
    compressed_uv_rot_anchor: list[u8] = ArrayOf(u8, 2)
    Padding(2)