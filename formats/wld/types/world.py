from enum import Flag
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *
from ...csv.types.csv import *
from ...ape.types.model import *

class WorldShapeType(Enum):
    POINT = 0
    LINE = 1
    SPLINE = 2
    BOX = 3
    SPHERE = 4
    CYLINDER = 5
    MESH = 6
    COUNT = 7

class PortalFlags(Flag):
    NONE                    = 0x0000
    CLOSED                  = 0x0001
    MIRRORED                = 0x0002
    ALWAYS_VISIBLE          = 0x0004
    ONE_WAY                 = 0x0008
    SOUND                   = 0x0010
    ANTIPORTAL              = 0x0020
    VISIBILITY              = 0x0040
    NORM_X_LARGEST          = 0x1000
    NORM_Y_LARGEST          = 0x2000
    NORM_Z_LARGEST          = 0x3000
    AUTO_PORTAL             = 0x8000
        
class FVisAABB_t(Struct):
    min_xyz: CFVec3 = Field(CFVec3)
    max_xyz: CFVec3 = Field(CFVec3)

class FVisCellTreeNode_t(Struct):
    aabb: FVisAABB_t = Field(FVisAABB_t)
    parent_node_idx: int = Field(u16)
    child_node_idx1: int = Field(u16)
    child_node_idx2: int = Field(u16)
    contained_cell_idx: int = Field(u16)

class FVisCellTree_t(Struct):
    first_node_index: int = Field(u16)
    node_count: int = Field(u16)
    nodes: Pointer[FVisCellTreeNode_t] = PointerTo(FVisCellTreeNode_t)

class FVisPortal_t(Struct):
    flags: PortalFlags = Field(EnumType(PortalFlags, 2))
    portal_id: int = Field(u16)
    adjacent_volume: list[int] = ArrayOf(u16, 2)
    idx_in_volume: list[int] = ArrayOf(u8, 2)
    vert_count: int = Field(u16)
    vertices: list[CFVec3] = ArrayOf(CFVec3, 4)
    normal: CFVec3 = Field(CFVec3)
    bounding_sphere_ws: CFSphere = Field(CFSphere)
    bounding_radius_sq: float = Field(f32)

class CFWorldKey(Struct):
    visited_key: list[int] = ArrayOf(u32, 3)

class FVisVolume_t(Struct):
    volume_id: int = Field(u16)
    flags: int = Field(u8)
    Padding(1)
    key: CFWorldKey = Field(CFWorldKey)
    bounding_sphere_ws: CFSphere = Field(CFSphere)
    portal_count: int = Field(u8)
    cell_count: int = Field(u8)
    cell_first_idx: int = Field(u16)
    crosses_planes_mask: int = Field(s8)
    active_adjacent_steps: int = Field(u8)
    active_step_decrement: int = Field(s8)
    Padding(1)
    Padding(2 * 4) # Runtime value
    Padding(16 * 4) # Runtime value
    portal_indices: Pointer[int] = PointerToIterable(u16, 'portal_count')
    world_geo_index: int = Field(u32)
    user_data: Pointer[None] = VoidPointer() # Seemingly unused for MA
    
class FVisPlane_t(Struct):
    normal: CFVec3A = Field(CFVec3A)
    point: CFVec3A = Field(CFVec3A)

class FVisCell_t(Struct):
    bounding_sphere_ws: CFSphere = Field(CFSphere)
    parent_volume_idx: int = Field(u16)
    plane_count: int = Field(u8)
    Padding(1)
    bounding_planes: IterablePointer[FVisPlane_t] = PointerToIterable(FVisPlane_t, 'plane_count')

class FVisData_t(Struct):
    portal_count: int = Field(u16)
    cell_count: int = Field(u16)
    volume_count: int = Field(u16)
    light_count: int = Field(u16)

    cell_tree: FVisCellTree_t = Field(FVisCellTree_t)
    ambient_light_color: CFColorRGB = Field(CFColorRGB)
    ambient_light_intensity: float = Field(f32)
    fog_start_z: float = Field(f32)
    fog_end_z: float = Field(f32)
    fog_motif: CFColorMotif = Field(CFColorMotif)
    portals: IterablePointer[FVisPortal_t] = PointerToIterable(FVisPortal_t, 'portal_count')
    volumes: IterablePointer[FVisVolume_t] = PointerToIterable(FVisVolume_t, 'volume_count')
    cells: IterablePointer[FVisCell_t] = PointerToIterable(FVisCell_t, 'cell_count')
    lights: IterablePointer[FLightInit_t] = PointerToIterable(FLightInit_t, 'light_count')

class FData_WorldInitHeader_t(Struct):
    num_init_structs: int = Field(u32)
    Padding(12)

class ColorStream_t(Struct):
    vb_index: int = Field(u16)
    color_count: int = Field(u16)
    vertex_colors: Pointer[None] = VoidPointer() #TODO

class CFWorldShapeLine(Struct):
    length: float = Field(f32)

class CFWorldShapeSpline(Struct):
    point_count: int = Field(u32)
    closed: bool = Field(BOOL)
    points: Pointer[CFVec3] = PointerToIterable(CFVec3, 'point_count')

class CFWorldShapeBox(Struct):
    dim_x: float = Field(f32)
    dim_y: float = Field(f32)
    dim_z: float = Field(f32)

class CFWorldShapeSphere(Struct):
    radius: float = Field(f32)

class CFWorldShapeCylinder(Struct):
    radius: float = Field(f32)
    dim_y: float = Field(f32)
    
class CFWorldShapeMesh(Struct):
    mesh_name: Pointer[str] = PointerTo(NullTermString())
    lightmap_name: list[Pointer[str]] = ArrayOf(PointerTo(NullTermString()), 4)
    lightmap_motifs: list[int] = ArrayOf(u16, 4)
    mesh_inst_flags: int = Field(u32)
    cull_dist_2: float = Field(f32)
    tint_rgb: CFColorRGB = Field(CFColorRGB)
    color_stream_count: int = Field(u8)
    Padding(3)
    color_streams: Pointer[ColorStream_t] = PointerTo(ColorStream_t)

class CFWorldShapeInit(Struct):
    shape_type: WorldShapeType = Field(EnumType(WorldShapeType, 4))
    BeginUnion()
    shape: Pointer[None] = VoidPointer()
    line: Pointer[CFWorldShapeLine] = PointerTo(CFWorldShapeLine)
    spline: Pointer[CFWorldShapeSpline] = PointerTo(CFWorldShapeSpline)
    box: Pointer[CFWorldShapeBox] = PointerTo(CFWorldShapeBox)
    sphere: Pointer[CFWorldShapeSphere] = PointerTo(CFWorldShapeSphere)
    cylinder: Pointer[CFWorldShapeCylinder] = PointerTo(CFWorldShapeCylinder)
    mesh: Pointer[CFWorldShapeMesh] = PointerTo(CFWorldShapeMesh)
    EndUnion()
    mtx: CFMtx43 = Field(CFMtx43)
    parent_shape_index: int = Field(s32)
    game_data: Pointer[FDataGamFile_Header_t] = PointerTo(FDataGamFile_Header_t)

class FData_WorldFileHeader_t(Struct):
    num_bytes: int = Field(u32)

    num_meshes: int = Field(u32)
    BeginUnion()
    offset_to_mesh_inits: int = Field(u32)
    mesh_inits: IterablePointer[int] = PointerToIterable(u32, 'num_meshes')
    EndUnion()
    offset_to_mesh_sizes: int = Field(u32)
    mesh_bytes: int = Field(u32)
    
    world_offset: int = Field(u32)
    world_bytes: int = Field(u32)
    streaming_data_offset: Pointer[None] = VoidPointerField()
    streaming_data_bytes: int = Field(u32)
    
    BeginUnion()
    init_offsets: int = Field(u32)
    init_header: Pointer[FData_WorldInitHeader_t] = PointerTo(FData_WorldInitHeader_t)
    EndUnion()

    init_bytes: int = Field(u32)