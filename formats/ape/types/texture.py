from enum import Flag

from ...common.types.common import CFVec2
from ....common.binary_reader import BinaryReader

class TexLayerIdFlags(Flag):
    NONE = 0x00
    USE_ST_INFO = 0x01
    USE_FLIP_INFO = 0x02
    BEGIN_SCROLLING = 0x04
    BEGIN_FLIPPING = 0x08
    BEGIN_ROTATING = 0x10

class FTexInfo_t:
    def __init__(self):
        self.tex_name = ""
        self.tex_fmt = 0
        self.pal_fmt = 0
        self.flags = 0
        self.lod_count = 0
        self.render_target_stencil_bit_count = 0
        self.render_target_depth_bit_count = 0
        self.texels_across = 0
        self.texels_down = 0

    def read(self, reader: BinaryReader):
        self.tex_name = reader.read_string(16)
        reader.skip(4) #userdata
        self.tex_fmt = reader.read_U8()
        self.pal_fmt = reader.read_U8()
        self.flags = reader.read_U8()
        self.lod_count = reader.read_U8()
        self.render_target_stencil_bit_count = reader.read_U8()
        self.render_target_depth_bit_count = reader.read_U8()
        reader.read_U8s(2)
        self.texels_across = reader.read_U16()
        self.texels_down = reader.read_U16()

class CFTexInst:
    def __init__(self):
        # 0x18 = 24 long
        pass

    def read(self, reader: BinaryReader):
        reader.skip(0x18)
        
class FShTexInst_t:
    def __init__(self):
        self.texture_name = ""
        self.tex_layer_id = 0

    def read(self, reader: BinaryReader):
        reader.skip(0x18) #CFTexInst
        
        texture_name_offset = reader.read_U16()
        with reader.detour(texture_name_offset):
            self.texture_name = reader.read_string()
        self.tex_layer_id = reader.read_U8()
        reader.skip(0x1) #PAD


class FMeshTexLayerID_t:
    def __init__(self):
        self.tex_layer_id = 0
        self.flags = TexLayerIdFlags.NONE
        self.flip_page_count = 0
        self.frames_per_flip = 0
        self.flip_palette = 0
        self.scroll_st_per_sec = CFVec2()
        self.uv_degree_rotation_per_sec = 0.0
        self.uv_rot_anchor = (0.0, 0.0)

    def read(self, reader: BinaryReader):
        self.tex_layer_id = reader.read_U8()
        self.flags = TexLayerIdFlags(reader.read_U8())
        
        self.flip_page_count = reader.read_U8()
        self.frames_per_flip = reader.read_U8()
        
        self.flip_palette = reader.read_U32()
        
        self.scroll_st_per_sec.read(reader)
        
        self.uv_degree_rotation_per_sec = reader.read_F32()
        
        compressed_uv_rot_anchor = reader.read_U8s(2)
        self.uv_rot_anchor = (compressed_uv_rot_anchor[0] / 255.0, compressed_uv_rot_anchor[1] / 255.0)
        reader.read_U8s(2) #PAD