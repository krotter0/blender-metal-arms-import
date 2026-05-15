
from ....common.binary_reader import BinaryReader
from ...common.types.common import CFSphere

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

class DXVertex:
    def __init__(self):
        self.pos: tuple[float, float, float] = None
        self.normals: list[tuple[float, float, float]] = None
        self.weights: list[float] = None
        self.colors: list[tuple[float, float, float, float]] = None
        self.uvs: list[tuple[float, float]] = None

    def read(self, reader: BinaryReader, vertex_format: FDX8VB_Info):
        start_pos = reader.tell()

        reader.seek(start_pos + vertex_format.offset_pos)
        self.pos = self._read_pos(reader)

        if vertex_format.weight_count != 255:
            reader.seek(start_pos + vertex_format.offset_weight)
            self.weights = self._read_weights(reader, vertex_format)

        if vertex_format.normal_count != 255:
            reader.seek(start_pos + vertex_format.offset_norm)
            self.normals = self._read_normals(reader, vertex_format)

        if vertex_format.color_count != 255:
            reader.seek(start_pos + vertex_format.offset_color)
            self.colors = self._read_colors(reader, vertex_format)

        if vertex_format.tc_count != 255:
            reader.seek(start_pos + vertex_format.offset_tc)
            self.uvs = self._read_tcs(reader, vertex_format)

        reader.seek(start_pos + vertex_format.vtx_bytes)

    def _read_tcs(self, reader: BinaryReader, vertex_format: FDX8VB_Info):
        return [reader.read_F32s(2) for _ in range(vertex_format.tc_count)]
    
    def _read_colors(self, reader: BinaryReader, vertex_format: FDX8VB_Info):
        colors = []
        for _ in range(vertex_format.color_count):
            r = reader.read_U8() / 255.0
            g = reader.read_U8() / 255.0
            b = reader.read_U8() / 255.0
            a = reader.read_U8() / 255.0
            colors.append((r, g, b, a))
        return colors
    
    def _read_weights(self, reader: BinaryReader, vertex_format: FDX8VB_Info):
        return [reader.read_F32() for _ in range(vertex_format.weight_count)]
    
    def _read_normals(self, reader: BinaryReader, vertex_format: FDX8VB_Info):
        return [reader.read_F32s(3) for _ in range(vertex_format.normal_count)]
    
    def _read_pos(self, reader: BinaryReader):
        return reader.read_F32s(3)

class FDX8BasisVectors_t:
    def __init__(self):
        self.tx = 0.0
        self.ty = 0.0
        self.tz = 0.0
        self.bx = 0.0
        self.by = 0.0
        self.bz = 0.0

    def read(self, reader: BinaryReader):
        self.tx = reader.read_F32()
        self.ty = reader.read_F32()
        self.tz = reader.read_F32()
        
        self.bx = reader.read_F32()
        self.by = reader.read_F32()
        self.bz = reader.read_F32()

class FDX8VB_t:
    def __init__(self):
        self.lmtc_count = 0
        self.lmuv_stream = 0
        self.basis: list[FDX8BasisVectors_t] = []
        self.info: FDX8VB_Info = None
        self.dynamic = False
        self.software_vp = False
        self.locked = False
        self.lock_buf = 0
        self.lock_offset = 0
        self.lock_bytes = 0
        self.vertex_shader = 0
        self.vb: list[DXVertex] = []

    def read(self, reader: BinaryReader):
        reader.skip(8) #FLink_t
        vtx_count = reader.read_U32()
        bytes_per_vertex = reader.read_U16()
        
        self.lmtc_count = reader.read_U16()
        self.lmuv_stream = reader.read_U32()
        self.basis = [FDX8BasisVectors_t() for _ in range(vtx_count)]
        reader.read_ptr_objects(self.basis)
        
        info_index = reader.read_S8()
        self.info = _VB_INFO_TABLE[info_index]
        self.dynamic = reader.read_BOOL8()
        self.software_vp = reader.read_BOOL8()
        
        self.locked = reader.read_BOOL8()
        self.lock_buf = reader.read_U32()
        
        self.lock_offset = reader.read_U32()
        self.lock_bytes = reader.read_U32()
        
        self.vertex_shader = reader.read_U32()
        
        dxvb = reader.read_U32()
        with reader.detour(dxvb):
            self.vb = [DXVertex() for _ in range(vtx_count)]
            for i in range(vtx_count):
                self.vb[i].read(reader, self.info)
                

class FDX8MeshTriList_t:
    def __init__(self):
        self.tri_count = 0
        self.start_vindex = 0
        self.vtx_index_min = 0
        self.vtx_index_range = 0

    def read(self, reader: BinaryReader):
        self.tri_count = reader.read_U16()
        self.start_vindex = reader.read_U16()
        self.vtx_index_min = reader.read_U16()
        self.vtx_index_range = reader.read_U16()
        
class FDX8MeshStrip_t:
    def __init__(self):
        self.tri_count = 0
        self.start_vindex = 0
        self.vtx_index_min = 0
        self.vtx_index_range = 0

    def read(self, reader: BinaryReader):
        self.tri_count = reader.read_U8()
        reader.read_U8() #__PAD
        self.start_vindex = reader.read_U16()
        self.vtx_index_min = reader.read_U16()
        self.vtx_index_range = reader.read_U16()
        
class FDX8MeshCluster_t:
    def __init__(self):
        self.flags = 0
        self.segment_idx = 0
        self.vb_index = 0
        self.ib_index = 0
        self.part_id = 0
        self.lod_id = 0
        self.push_buffer = 0
        self.tri_list = FDX8MeshTriList_t()
        self.strip_buffers: list[FDX8MeshStrip_t] = []
        
    def read(self, reader: BinaryReader):
        strip_count = reader.read_U16()
        self.flags = reader.read_U8()
        self.segment_idx = reader.read_U8()
        self.vb_index = reader.read_U8()
        self.ib_index = reader.read_U8()
        self.part_id = reader.read_U8()
        self.lod_id = reader.read_U8()
        
        self.push_buffer = reader.read_U32() #missing from old models?
        self.tri_list.read(reader)

        strip_buffer = reader.read_U32()
        with reader.detour(strip_buffer):
            self.strip_buffers = []
            for _ in range(strip_count):
                v = FDX8MeshStrip_t()
                v.read(reader)
                self.strip_buffers.append(v)

class FDX8MeshMaterial_t:
    def __init__(self):
        self.clusters: list[FDX8MeshCluster_t] = []
        
    def read(self, reader: BinaryReader):
        cluster_ptr = reader.read_U32()
        cluster_count = reader.read_U32()
        
        with reader.detour(cluster_ptr):
            self.clusters: list[FDX8MeshCluster_t] = []
            for _ in range(cluster_count):
                v = FDX8MeshCluster_t()
                v.read(reader)
                self.clusters.append(v)

class FDX8Mesh_t:
    def __init__(self):
        self.flags = 0
        self.vb_count = 0
        self.ib_count = 0
        self.disposable_offset = 0
        self.at_rest_bound_sphere_ms = CFSphere()
        self.mesh = 0
        self.vb: list[FDX8VB_t] = []
        self.coll_vert_buffer = 0
        self.indices: list[list[int]] = []
        
    def read(self, reader: BinaryReader):
        self.flags = reader.read_U16()
        self.vb_count = reader.read_U8()
        self.ib_count = reader.read_U8()
        self.disposable_offset = reader.read_U32()
        
        self.at_rest_bound_sphere_ms.read(reader)
        
        self.mesh = reader.read_U32()
        
        self.vb = [FDX8VB_t() for _ in range(self.vb_count)]
        reader.read_ptr_objects(self.vb)
        self.coll_vert_buffer = reader.read_U32()
        indices_counts_pointer = reader.read_U32()
        
        dxibs_ptr = reader.read_U32()

        indices_counts = None
        with reader.detour(indices_counts_pointer):
            indices_counts = reader.read_U16s(self.ib_count)
        
        with reader.detour(dxibs_ptr):
            indices_pointers = reader.read_U32s(self.ib_count)
            self.indices = []
            for i,p in enumerate(indices_pointers):
                reader.seek(p)
                self.indices.append(reader.read_U16s(indices_counts[i]))