from ...structs.structs import *
from ..common.types.common import *

class FDX8VB_Info:
    def __init__(self,
        vtx_bytes: int,
        unlit: bool,
        normal_count: int,
        weight_count: int,
        color_count: int,
        tc_count: int,
        offset_pos: int,
        offset_weight: int,
        offset_norm: int,
        offset_color: int,
        offset_tc: int
    ):
        self.vtx_bytes = vtx_bytes
        self.unlit = unlit
        self.normal_count = normal_count
        self.weight_count = weight_count
        self.color_count = color_count
        self.tc_count = tc_count
        self.offset_pos = offset_pos
        self.offset_weight = offset_weight
        self.offset_norm = offset_norm
        self.offset_color = offset_color
        self.offset_tc = offset_tc
        
_VB_INFO_TABLE = [
    FDX8VB_Info(
        vtx_bytes=36,
        unlit=False,
        normal_count=1,
        weight_count=0,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=255,
        offset_norm=12,
        offset_color=24,
        offset_tc=28,
    ),
    FDX8VB_Info(
        vtx_bytes=44,
        unlit=False,
        normal_count=1,
        weight_count=0,
        color_count=1,
        tc_count=2,
        offset_pos=0,
        offset_weight=255,
        offset_norm=12,
        offset_color=24,
        offset_tc=28,
    ),
    FDX8VB_Info(
        vtx_bytes=48,
        unlit=False,
        normal_count=1,
        weight_count=3,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=12,
        offset_norm=24,
        offset_color=36,
        offset_tc=40,
    ),
    FDX8VB_Info(
        vtx_bytes=56,
        unlit=False,
        normal_count=1,
        weight_count=3,
        color_count=1,
        tc_count=2,
        offset_pos=0,
        offset_weight=12,
        offset_norm=24,
        offset_color=36,
        offset_tc=40,
    ),
    FDX8VB_Info(
        vtx_bytes=40,
        unlit=True,
        normal_count=0,
        weight_count=0,
        color_count=2,
        tc_count=2,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=16,
        offset_tc=24,
    ),
    FDX8VB_Info(
        vtx_bytes=16,
        unlit=False,
        normal_count=0,
        weight_count=0,
        color_count=1,
        tc_count=0,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=12,
        offset_tc=255,
    ),
    FDX8VB_Info(
        vtx_bytes=24,
        unlit=False,
        normal_count=0,
        weight_count=0,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=12,
        offset_tc=16,
    )
]

class DXVertexFormat0(Struct):
    EXPECTED_SIZE = 36
    pos: CFVec3 = Field(CFVec3)
    weights = None
    normals: CFVec3 = ArrayOf(Field(CFVec3), 1)
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 1)

class DXVertexFormat1(Struct):
    EXPECTED_SIZE = 44
    pos: CFVec3 = Field(CFVec3)
    weights = None
    normals: CFVec3 = ArrayOf(Field(CFVec3), 1)
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 2)

class DXVertexFormat2(Struct):
    EXPECTED_SIZE = 48
    pos: CFVec3 = Field(CFVec3)
    weights: list[float] = ArrayOf(Field(f32), 3)
    normals: CFVec3 = ArrayOf(Field(CFVec3), 1)
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 1)

class DXVertexFormat3(Struct):
    EXPECTED_SIZE = 56
    pos: CFVec3 = Field(CFVec3)
    weights: list[float] = ArrayOf(Field(f32), 3)
    normals: CFVec3 = ArrayOf(Field(CFVec3), 1)
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 2)

class DXVertexFormat4(Struct):
    EXPECTED_SIZE = 40
    pos: CFVec3A = Field(CFVec3A)
    weights = None
    normals = None
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 2)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 2)

class DXVertexFormat5(Struct):
    EXPECTED_SIZE = 16
    pos: CFVec3 = Field(CFVec3)
    weights = None
    normals = None
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs = None

class DXVertexFormat6(Struct):
    EXPECTED_SIZE = 24
    pos: CFVec3 = Field(CFVec3)
    weights = None
    normals = None
    colors: CFColorPackedRGBA = ArrayOf(Field(CFColorPackedRGBA), 1)
    uvs: list[CFVec2] = ArrayOf(Field(CFVec2), 1)


_VB_TYPE_TABLE = [
    DXVertexFormat0,
    DXVertexFormat1,
    DXVertexFormat2,
    DXVertexFormat3,
    DXVertexFormat4,
    DXVertexFormat5,
    DXVertexFormat6
]

DXVertexFormat = DXVertexFormat0 | DXVertexFormat1 | DXVertexFormat2 | DXVertexFormat3 | DXVertexFormat4 | DXVertexFormat5 | DXVertexFormat6

def get_vb_info(info_index: int) -> FDX8VB_Info:
    if info_index < 0 or info_index >= len(_VB_INFO_TABLE):
        raise ValueError(f"Invalid vb info index: {info_index}")
    return _VB_INFO_TABLE[info_index]

def get_vb_vertex_type(info_index: int) -> DXVertexFormat:
    if info_index < 0 or info_index >= len(_VB_TYPE_TABLE):
        raise ValueError(f"Invalid vb info index: {info_index}")
    return _VB_TYPE_TABLE[info_index]