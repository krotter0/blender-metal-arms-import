
from enum import Enum, Flag
from .common import CFSphere, CFColorMotif, CFMtx43
from ....common.binary_reader import BinaryReader

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

class FLightInit_t:
    def __init__(self):
        self.name = ""
        self.perpixel_tex_name = ""
        self.corona_tex_name = ""
        self.flags: LightFlags = LightFlags.NONE
        self.light_id = 0xFFFF
        self.type: LightType = LightType.DIRECTIONAL
        self.parent_bone_idx = -1
        self.intensity = 0.0
        self.motif = CFColorMotif()
        self.influence = CFSphere()
        self.mtx_orientation = CFMtx43()
        self.spot_inner_radians = 0.0
        self.spot_outer_radians = 0.0
        self.corona_scale = 0.0

    def read(self, reader: BinaryReader):
        self.name = reader.read_string(16)
        self.perpixel_tex_name = reader.read_string(16)
        self.corona_tex_name = reader.read_string(16)
        self.flags = LightFlags(reader.read_U32())
        self.light_id = reader.read_U16()
        self.type = LightType(reader.read_U8())
        self.parent_bone_idx = reader.read_S8()
        self.intensity = reader.read_F32()
        self.motif.read(reader)
        self.influence.read(reader)
        self.mtx_orientation.read(reader)
        self.spot_inner_radians = reader.read_F32()
        self.spot_outer_radians = reader.read_F32()
        self.corona_scale = reader.read_F32()