from enum import Enum, Flag

from ....common.platform import Platform
from ....common.binary_reader import BinaryReader
from ...common.types.common import CFSphere

_POS_FRAC_ADJUST = [(1.0 / (1 << i)) for i in range(16)]

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

class GXPrimitiveType(Flag):
    TRIANGLESTRIP = 0x98
    TRIANGLES = 0x90

class GCVertex:
    def __init__(self, pos=None, normals=None, weights=None, colors=None, uvs=None):
        self.pos: tuple[float, float, float] = pos
        self.normals: list[tuple[float, float, float]] = normals
        self.weights: list[float] = weights
        self.colors: list[tuple[float, float, float, float]] = colors
        self.uvs: list[tuple[float, float]] = uvs

class GCDisplayListPrimitive:
    def __init__(self, primitive_type: GXPrimitiveType, indices_count: int, pos_indices: list[int], normal_indices: list[int] | None, binormal_indices: list[int] | None, tangent_indices: list[int], diffuse_indices: list[int] | None, st_indices: list[list[int]]):
        self.primitive_type = primitive_type
        self.num_indices = indices_count
        self.pos_indices = pos_indices
        self.normal_indices = normal_indices
        self.binormal_indices = binormal_indices
        self.tangent_indices = tangent_indices
        self.diffuse_indices = diffuse_indices
        self.st_indices = st_indices

class FGCColor_t:
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0
        self.a = 0

    def read(self, reader: BinaryReader):
        self.r = reader.read_U8()
        self.g = reader.read_U8()
        self.b = reader.read_U8()
        self.a = reader.read_U8()

class FGCST16_t:
    def __init__(self):
        self.s = 0
        self.t = 0

    def read(self, reader: BinaryReader):
        self.s = reader.read_U16()
        self.t = reader.read_U16()

class FGCNBT8_t:
    def __init__(self):
        self.nx = 0
        self.ny = 0
        self.nz = 0

        self.bx = 0
        self.by = 0
        self.bz = 0
        
        self.tx = 0
        self.ty = 0
        self.tz = 0

    def read(self, reader: BinaryReader):
        self.nx = reader.read_S8()
        self.ny = reader.read_S8()
        self.nz = reader.read_S8()

        self.bx = reader.read_S8()
        self.by = reader.read_S8()
        self.bz = reader.read_S8()

        self.tx = reader.read_S8()
        self.ty = reader.read_S8()
        self.tz = reader.read_S8()

class FGCMeshSkin_t:
    def __init__(self):
        self.trans_desc_count = 0
        self.td1mtx_count = 0
        self.td2mtx_count = 0
        self.td3or4mtx_count = 0
        self.trans_desc = 0
        self.skinned_verts_count = 0
        self.skinned_verts = 0
        self.skin_weights = 0

    def read(self, reader: BinaryReader):
        self.trans_desc_count = reader.read_U16()
        self.td1mtx_count = reader.read_U16()
        self.td2mtx_count = reader.read_U16()
        self.td3or4mtx_count = reader.read_U16()
        self.trans_desc = reader.read_U32() #TODO
        self.skinned_verts_count = reader.read_U32()
        self.skinned_verts = reader.read_U32() #TODO
        self.skin_weights = reader.read_U32() #TODO

class FGCMesh_t:
    def __init__(self):
        self.at_rest_bound_sphere_ms = CFSphere()
        self.flags = 0
        self.vb_count = 0
        self.mtl_count = 0
        self.vb: list[FGCVB_t] = []
        self.mesh_skin: FGCMeshSkin_t = None

    def read(self, reader: BinaryReader):
        reader.skip(4) # Ape ptr
        self.at_rest_bound_sphere_ms.read(reader)
        self.flags = reader.read_U8()
        self.vb_count = reader.read_U8()
        self.mtl_count = reader.read_U16()

        self.vb = [FGCVB_t() for _ in range(self.vb_count)]
        reader.read_ptr_objects(self.vb)

        self.mesh_skin = None
        mesh_skin_ptr = reader.read_U32()
        if mesh_skin_ptr != 0:
            with reader.detour(mesh_skin_ptr):
                self.mesh_skin = FGCMeshSkin_t()
                self.mesh_skin.read(reader)

class FGCVB_t:
    def __init__(self):
        self.flags = GCVBFlags.NONE
        self.pos_count = 0
        self.pos_type = GCVertexPositionType.U8
        self.pos_idx_type = GCVertexAttributeType.NONE
        self.pos_stride = 0
        self.pos_frac = 1.0
        self.diffuse_count = 0
        self.color_idx_type = GCVertexAttributeType.NONE
        self.gc_vertex_format = GCVertexFormat.VTXFMT0

        self.positions: list[tuple[float, float, float]] = None
        self.diffuses: list[FGCColor_t] = None
        self.sts: list[FGCST16_t] = None
        self.nbt: list[FGCNBT8_t] = None

    def read(self, reader: BinaryReader):
        self.flags = GCVBFlags(reader.read_U16())
        self.pos_count = reader.read_U16()
        self.pos_type = GCVertexPositionType(reader.read_U8())
        self.pos_idx_type = GCVertexAttributeType(reader.read_U8())
        self.pos_stride = reader.read_U8()
        self.pos_frac = _POS_FRAC_ADJUST[reader.read_U8()]
        self.diffuse_count = reader.read_U16()
        self.color_idx_type = GCVertexAttributeType(reader.read_U8())
        self.gc_vertex_format = GCVertexFormat(reader.read_U8())

        position_ptr = reader.read_U32()
        self.positions = None
        if position_ptr != 0:
            with reader.detour(position_ptr):
                self.positions = self._read_points(reader)

        self.diffuses = [FGCColor_t() for _ in range(self.diffuse_count)]
        reader.read_ptr_objects(self.diffuses)
        
        self.sts = None
        self._sts_ptr = reader.read_U32()

        self.nbt = None
        self._nbt_ptr = reader.read_U32()

    def _read_nbt(self, reader: BinaryReader, count: int):
        if self._nbt_ptr == 0:
            return
        
        with reader.detour(self._nbt_ptr):
            self.nbt = []
            for _ in range(count):
                nbt = FGCNBT8_t()
                nbt.read(reader)
                self.nbt.append(nbt)

    def _read_sts(self, reader: BinaryReader, count: int):
        if self._sts_ptr == 0:
            return
        
        with reader.detour(self._sts_ptr):
            self.sts = []
            for _ in range(count):
                st = FGCST16_t()
                st.read(reader)
                self.sts.append(st)

    def _get_point_reader_func(self):
        if self.pos_type == GCVertexPositionType.U8:
            return BinaryReader.read_U8s
        elif self.pos_type == GCVertexPositionType.S8:
            return BinaryReader.read_S8s
        elif self.pos_type == GCVertexPositionType.U16:
            return BinaryReader.read_U16s
        elif self.pos_type == GCVertexPositionType.S16:
            return BinaryReader.read_S16s
        elif self.pos_type == GCVertexPositionType.F32:
            return BinaryReader.read_F32s
        else:
            raise ValueError(f"Invalid vertex position type: {self.pos_type}")

    def _read_points(self, reader: BinaryReader):
        point_reader_func = self._get_point_reader_func()
        points = []
        for _ in range(self.pos_count):
            x, y, z = point_reader_func(reader, 3)
            x *= self.pos_frac
            y *= self.pos_frac
            z *= self.pos_frac
            points.append((x, y, z))
        return points

class FGCMeshMaterial_t:
    def __init__(self):
        self.dl_containers: list[FGC_DLCont_t] = []

    def read(self, reader: BinaryReader):
        dl_container_ptr = reader.read_U32()
        dl_container_count = reader.read_U16()
        
        self.dl_containers = [FGC_DLCont_t() for _ in range(dl_container_count)]
        with reader.detour(dl_container_ptr):
            for dl_container in self.dl_containers:
                dl_container.read(reader)

class FGC_DLCont_t:
    def __init__(self):
        self.flags = GCDLContFlags.NONE
        self.matrix_idx = 0
        self.lod_id = 0
        self.part_id = 0
        self.strip_tri_count = 0
        self.list_tri_count = 0
        self.strip_count = 0
        self.list_count = 0
        self.vb_index = 0
        self.size = 0
        self.buffer: bytes = None
        self.constant_color = FGCColor_t()

    def read(self, reader: BinaryReader):
        self.flags = GCDLContFlags(reader.read_U8())
        self.matrix_idx = reader.read_U8()
        self.lod_id = reader.read_U8()
        self.part_id = reader.read_U8()
        self.strip_tri_count = reader.read_U16()
        self.list_tri_count = reader.read_U16()
        self.strip_count = reader.read_U16()
        self.list_count = reader.read_U8()
        self.vb_index = reader.read_U8()
        self.size = reader.read_U32()
        buffer_ptr = reader.read_U32()
        if buffer_ptr != 0: 
            with reader.detour(buffer_ptr):
                self.buffer = reader.read_binary(self.size)
        self.constant_color.read(reader)

    def read_buffer(self, material, vbs: list[FGCVB_t]):
        vb = vbs[self.vb_index]

        primitives: list[GCDisplayListPrimitive] = []
        if self.flags & GCDLContFlags.STREAMING:
            return [] #TODO: Buffer is null when streaming flag is set
        with BinaryReader(self.buffer, big_endian=Platform.GC.is_big_endian()) as reader:
            primitive_count = self.strip_count + self.list_count
            while primitive_count > 0:
                primitive_count -= 1
                opcode = reader.read_U8()

                vtx_fmt = GCVertexFormat(opcode & 0x7)
                primitive_type = GXPrimitiveType(opcode & 0xF8)
                assert primitive_type in (GXPrimitiveType.TRIANGLESTRIP, GXPrimitiveType.TRIANGLES), f"GX DisplayList Opcode is neither of the expected primitive types: {opcode}"

                num_indices = reader.read_U16()

                has_nbt = vb.flags & GCVBFlags.NORM_NBT and self.flags & GCDLContFlags.STREAMING
                has_color = not self.flags & GCDLContFlags.CONSTANT_COLOR

                st_sets = material.base_st_sets + material.lightmap_st_sets

                pos_indices = []
                normal_indices = []
                binormal_indices = [] if has_nbt else None
                tangent_indices = [] if has_nbt else None
                diffuse_indices = [] if has_color else None
                st_indices = [[] for _ in range(st_sets)]
                for _ in range(num_indices):
                    if vb.pos_idx_type == GCVertexAttributeType.INDEX8:
                        pos_idx = reader.read_U8()
                    else:
                        pos_idx = reader.read_U16()
                    pos_indices.append(pos_idx)

                    norm_idx = reader.read_U16()
                    normal_indices.append(norm_idx)

                    binormal_idx, tangent_idx, diffuse_idx = None, None, None
                    if has_nbt:
                        binormal_idx = reader.read_U16()
                        binormal_indices.append(binormal_idx)
                        tangent_idx = reader.read_U16()
                        tangent_indices.append(tangent_idx)

                    if has_color:
                        if vb.color_idx_type == GCVertexAttributeType.INDEX8:
                            diffuse_idx = reader.read_U8()
                        else:
                            diffuse_idx = reader.read_U16()
                        diffuse_indices.append(diffuse_idx)

                    for j in range(st_sets):
                        st_idx = reader.read_U16()
                        st_indices[j].append(st_idx)

                primitive = GCDisplayListPrimitive(primitive_type, num_indices, pos_indices, normal_indices, binormal_indices, tangent_indices, diffuse_indices, st_indices)
                primitives.append(primitive)

        return primitives