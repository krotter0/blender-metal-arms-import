from .skeleton import *
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from ...common.types.light import *
from .texture import *

class FDX8BasisVectors_t(Struct):
    tx: float = Field(f32)
    ty: float = Field(f32)
    tz: float = Field(f32)

    bx: float = Field(f32)
    by: float = Field(f32)
    bz: float = Field(f32)

class FDX8VB_t(Struct):
    link: FLink_t = Field(FLink_t)
    vtx_count: int = Field(u32)
    bytes_per_vertex: int = Field(u16)
    lmtc_count: int = Field(u16)
    lmuv_stream: Pointer[None] = VoidPointer()
    basis_stream: Pointer[FDX8BasisVectors_t] = PointerTo(FDX8BasisVectors_t)
    info_index: int = Field(s8)
    dynamic: bool = Field(BOOL8)
    software_vp: bool = Field(BOOL8)
    locked: bool = Field(BOOL8)
    lock_buf: int = Field(u32)
    lock_offset: int = Field(u32)
    lock_bytes: int = Field(u32)
    vertex_shader: int = Field(u32)
    dxvb: Pointer[None] = VoidPointer()

class FDX8MeshTriList_t(Struct):
    tri_count: int = Field(u16)
    start_vindex: int = Field(u16)
    vtx_index_min: int = Field(u16)
    vtx_index_range: int = Field(u16)
        
class FDX8MeshStrip_t(Struct):
    tri_count: int = Field(u8)
    Padding(1)
    start_vindex: int = Field(u16)
    vtx_index_min: int = Field(u16)
    vtx_index_range: int = Field(u16)
        
class FDX8MeshCluster_t(Struct):
    strip_count: int = Field(u16)
    flags: int = Field(u8)
    segment_idx: int = Field(u8)
    vb_index: int = Field(u8)
    ib_index: int = Field(u8)
    part_id: int = Field(u8)
    lod_id: int = Field(u8)
    push_buffer: Pointer[None] = VoidPointer()
    tri_list: FDX8MeshTriList_t = Field(FDX8MeshTriList_t)
    strip_buffers: IterablePointer[FDX8MeshStrip_t] = PointerToIterable(FDX8MeshStrip_t, 'strip_count')

class FDX8MeshMaterial_t(Struct):
    clusters: IterablePointer[FDX8MeshCluster_t] = PointerToIterable(FDX8MeshCluster_t, 'cluster_count')
    cluster_count: int = Field(u32)

class FDX8Mesh_t(Struct):
    flags: int = Field(u16)
    vb_count: int = Field(u8)
    ib_count: int = Field(u8)
    disposable_offset: int = Field(u32)
    at_rest_bound_sphere_ms: CFSphere = Field(CFSphere)
    mesh: int = Field(u32)
    vb: Pointer[FDX8VB_t] = PointerToIterable(FDX8VB_t, 'vb_count')
    coll_vert_buffer: Pointer[Pointer[CFVec3]] = PointerTo(PointerTo(CFVec3))
    indices_count: IterablePointer[Pointer[u16]] = PointerToIterable(u16, 'ib_count')
    dxibs: IterablePointer[Pointer[u16]] = PointerToIterable(PointerTo(u16), 'ib_count')

    
# Beta struct differences
class FDX8MeshCluster_t_Beta(Struct):
    strip_count: int = Field(u16)
    flags: int = Field(u8)
    segment_idx: int = Field(u8)
    vb_index: int = Field(u8)
    ib_index: int = Field(u8)
    part_id: int = Field(u8)
    lod_id: int = Field(u8)
    tri_list: FDX8MeshTriList_t = Field(FDX8MeshTriList_t)
    strip_buffers: IterablePointer[FDX8MeshStrip_t] = PointerToIterable(FDX8MeshStrip_t, 'strip_count')

class FDX8MeshMaterial_t_Beta(Struct):
    clusters: IterablePointer[FDX8MeshCluster_t_Beta] = PointerToIterable(FDX8MeshCluster_t_Beta, 'cluster_count')
    cluster_count: int = Field(u32)