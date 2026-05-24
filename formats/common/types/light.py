from enum import Enum, Flag
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from .common import *

class LightFlags(Flag):
    NONE                    = 0x00000000
    ENABLE                  = 0x00000001
    HASDIR                  = 0x00000002
    HASPOS                  = 0x00000004
    LIGHT_ATTACHED          = 0x00000008
    NOLIGHT_TERRAIN         = 0x00000010
    DONT_LIGHT_UNATTACHED   = 0x00000020
    PER_PIXEL               = 0x00000040
    MESH_MUST_BE_PER_PIXEL  = 0x00000080
    ENGINE_LIGHT            = 0x00000100
    LIGHTMAP_LIGHT          = 0x00000200
    UNIQUE_LIGHTMAPS        = 0x00000400
    CORONA                  = 0x00000400
    CORONA_PROXFADE         = 0x00000800
    CORONA_ONLY             = 0x00001000
    CAST_SHADOWS            = 0x00002000
    CORONA_WORLDSPACE       = 0x00004000
    GAMEPLAY_LIGHT          = 0x00008000
    DYNAMIC_ONLY            = 0x40000000
    INCLUDE                 = 0x80000000

class LightType(Enum):
    DIRECTIONAL = 0
    OMNIDIRECTIONAL = 1
    SPOT = 2
    AMBIENT = 3
    COUNT = 4
    
class FLightInit_t(Struct):
    name: str = Field(FixedSizeString(16))
    perpixel_tex_name: str = Field(FixedSizeString(16))
    corona_tex_name: str = Field(FixedSizeString(16))
    flags: LightFlags = Field(EnumType(LightFlags, 4))
    light_id: int = Field(u16)
    type: LightType = Field(EnumType(LightType, 1))
    parent_bone_idx: int = Field(s8)
    intensity: float = Field(f32)
    motif: CFColorMotif = Field(CFColorMotif)
    influence: CFSphere = Field(CFSphere)
    mtx_orientation: CFMtx43 = Field(CFMtx43)
    spot_inner_radians: float = Field(f32)
    spot_outer_radians: float = Field(f32)
    corona_scale: float = Field(f32)