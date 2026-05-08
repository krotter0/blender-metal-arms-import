from enum import Enum, Flag

from ..csv.reader import FDataGamFile_Header_t
from ..ape.reader import Ape
from ..common.reader import BinaryReader, CFColorMotif, CFColorRGB, CFMtx43, CFSphere, CFVec3, CFVec3A, FLinkRoot_s

class WorldShapeType(Enum):
    POINT = 0
    LINE = 1
    SPLINE = 2
    BOX = 3
    SPHERE = 4
    CYLINDER = 5
    MESH = 6
    COUNT = 7

class LightType(Enum):
    DIRECTIONAL = 0
    OMNIDIRECTIONAL = 1
    SPOT = 2
    AMBIENT = 3
    COUNT = 4

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

class World:
    def __init__(self):
        self.vis_data = FVisData_t()
        self.worldshapes: list[CFWorldShapeInit] = []

    def read(self, reader: BinaryReader):
        num_bytes = reader.read_U32()
        num_meshes = reader.read_U32()
        offset_to_mesh_inits = reader.read_U32()
        offset_to_mesh_sizes = reader.read_U32()
        mesh_bytes = reader.read_U32()
        world_offset = reader.read_U32()
        world_bytes = reader.read_U32()
        streaming_data_offset = reader.read_U32()
        streaming_data_bytes = reader.read_U32()
        init_offsets = reader.read_U32()
        init_bytes = reader.read_U32()
        
        reader.seek(offset_to_mesh_inits)
        mesh_pointers = reader.read_U32s(num_meshes)
        self.meshes = []
        for p in mesh_pointers:
            ape = Ape()
            reader.set_offset(p)
            reader.seek(0)
            ape.read(reader)
            self.meshes.append(ape)
                
        reader.set_offset(world_offset)
        reader.seek(0)
        self.vis_data.read(reader)
        
        reader.set_offset(init_offsets)
        reader.seek(0)
        world_init_header = FData_WorldInitHeader_t()
        world_init_header.read(reader)

        reader.set_offset(0)
        reader.set_offset(reader.tell())
        for _ in range(world_init_header.num_init_structs):
            shape = CFWorldShapeInit()
            shape.read(reader)
            self.worldshapes.append(shape)

        reader.set_offset(0)
        
class FVisAABB_t:
    def __init__(self):
        self.min_xyz = CFVec3()
        self.max_xyz = CFVec3()

    def read(self, reader: BinaryReader):
        self.min_xyz.read(reader)
        self.max_xyz.read(reader)

class FVisCellTreeNode_t:
    def __init__(self):
        self.aabb = FVisAABB_t()
        self.parent_node_idx = 0
        self.child_node_idx1 = 0
        self.child_node_idx2 = 0
        self.contained_cell_idx = 0

    def read(self, reader: BinaryReader):
        """
        FVisAABB_t AABB;			// Axis aligned bounding box that describes this leaf
        u16 nParentNodeIdx;			// index of the parent of this node
        u16 nChildNodeIdx1;			// index of the first child or 0xffff if there is no child
        u16 nChildNodeIdx2;			// index of the second child or 0xffff if there is no child
        u16 nContainedCellIdx;		// Index of cell contained within this node, or 0xffff
        """
        self.aabb.read(reader)
        self.parent_node_idx = reader.read_U16()
        self.child_node_idx1 = reader.read_U16()
        self.child_node_idx2 = reader.read_U16()
        self.contained_cell_idx = reader.read_U16()

class FVisCellTree_t:
    def __init__(self):
        self.first_node_index = 0
        self.nodes = []

    def read(self, reader: BinaryReader):
        """
        u16 nFirstNodeIndex;			// index of the first node
        u16 nNodeCount;					// number of nodes in the tree
        FVisCellTreeNode_t *paNodes;	// pointer to the array of nodes
        """
        self.first_node_index = reader.read_U16()
        node_count = reader.read_U16()
        self.nodes = [FVisCellTreeNode_t() for _ in range(node_count)]
        reader.read_ptr_objects(self.nodes)

class FVisPortal_t:
    """
	u16 nFlags; 				// See FVisPortal flags, above
	u16 nPortalID;				// Index of this portal in the portal data portal list (used at the app level to identify portals)

	// Connectivity description
	u16 anAdjacentVolume[2];	// The indices of the two adjacent volumes into the global volume array
	u8  anIdxInVolume[2];		// The portal's portal index in the portal arrays of the adjacent volumes
	u16 nVertCount;
	
	CFVec3 avVertices[FVIS_MAX_PORTAL_VERTS];	// The coplanar verts that form the portal (MUST WIND CLOCKWISE WHEN NORMAL FACING VIEWPOINT)
	CFVec3 vNormal;				// The world space normal of the portal pointing into volume index 0 (negate for the normal into volume 1) (Could be index into normal sphere for GC)
	CFSphere spBoundingWS;		// A world space bounding sphere
	f32 fBoundingRadiusSq;		// Square of the bounding sphere radius
    """
    def __init__(self):
        self.flags: PortalFlags = PortalFlags.NONE
        self.portal_id = 0
        self.adjacent_volume = [0, 0]
        self.idx_in_volume = [0, 0]
        self.verticies = []
        self.normal = CFVec3()
        self.bounding_sphere_ws = CFSphere()
        self.bounding_radius_sq = 0.0

    def read(self, reader: BinaryReader):
        self.flags = PortalFlags(reader.read_U16())
        self.portal_id = reader.read_U16()
        self.adjacent_volume = reader.read_U16s(2)
        self.idx_in_volume = reader.read_U8s(2)

        nVertCount = reader.read_U16()
        self.verticies = [CFVec3() for _ in range(nVertCount)]
        for v in self.verticies:
            v.read(reader)
        for _ in range(4 - nVertCount):
            reader.skip(3 * 4) # Skip unused vertex slots

        self.normal = CFVec3()
        self.normal.read(reader)
        self.bounding_sphere_ws.read(reader)
        self.bounding_radius_sq = reader.read_F32()

class CFWorldKey:
    def __init__(self):
        self.m_anVisitedKey = [0] * 3

    def read(self, reader: BinaryReader):
        self.m_anVisitedKey = reader.read_U32s(3)
class FVisVolume_t:
    """
	u16 nVolumeID;					// Unique ID for this volume.  Should equal the index of this volume in the portal data volume array
	u8 nFlags;		
	CFWorldKey Key;					// Key to help with list processing
	CFSphere spBoundingWS;			// Bounding sphere for the volume in world space (used for frustum culling - eventually we should use a better shape)
	
	u8 nPortalCount;				// Number of portals in this volume
	u8 nCellCount;					// Number of cells that make up this volume
	u16 nCellFirstIdx;				// First Cell index in the array of cells
	
	s8 nCrossesPlanesMask;			// Used to indicate which frustum planes this volume crosses (must be set to 0 by tools)
	u8 nActiveAdjacentSteps;		// Number of steps from this volume, if drawn, that volumes will be added to the active list
	s8 nActiveStepDecrement;		// Decrement to active list stepping when adding this volume
	u8 __nPad;
	
	u16 anTotalTrackerCount[FWORLD_TRACKERTYPE_COUNT];	// Total number of trackers intersecting this volume (must be set to 0 by tools)
	FLinkRoot_t aTrackerIntersects[FWORLD_TRACKERTYPE_COUNT];	// World Intersects that indicate Trackers that currently intersect with this volume
	
	u16 *paPortalIndices;			// Pointer to the array of indices for portals that are visible in this volume

	CFMeshInst *pWorldGeo;			// World (static) geometry associated with this volume (The tool should store an index into the geo array which
									// will be resolved to a pointer to the actual geometry.  If there is no geo, this MUST be set to FVIS_INVALID_GEO_ID
									// by the tool.  The engine will then set it to NULL at load time.)
	
	void *pUserData;				// Pointer that the app can use to store information specific to this portal (ex. AI path nodes, etc)"""
    def __init__(self):
        self.nVolumeID = 0
        self.nFlags = 0
        self.Key = CFWorldKey()
        self.spBoundingWS = CFSphere()
        self.nPortalCount = 0
        self.nCellCount = 0
        self.nCellFirstIdx = 0
        self.nCrossesPlanesMask = 0
        self.nActiveAdjacentSteps = 0
        self.nActiveStepDecrement = 0
        self.paPortalIndices = []
        self.pWorldGeo = None

    def read(self, reader: BinaryReader):
        self.nVolumeID = reader.read_U16()
        self.nFlags = reader.read_U8()
        reader.skip(1) # Padding
        self.Key.read(reader)
        self.spBoundingWS.read(reader)
        self.nPortalCount = reader.read_U8()
        self.nCellCount = reader.read_U8()
        self.nCellFirstIdx = reader.read_U16()
        self.nCrossesPlanesMask = reader.read_S8()
        self.nActiveAdjacentSteps = reader.read_U8()
        self.nActiveStepDecrement = reader.read_S8()
        reader.skip(1) # Padding
        reader.skip(2 * 4) # Runtime value
        reader.skip(16 * 4) # Runtime value
        
        portalIndicesPtr = reader.read_U32()
        if portalIndicesPtr != 0:
            with reader.detour(portalIndicesPtr):
                self.paPortalIndices = reader.read_U16s(self.nPortalCount)

        self.WorldGeoIndex = reader.read_U32()
        reader.skip(4) # User data, seemingly unused for MA

class FVisPlane_t:
    def __init__(self):
        self.normal = CFVec3A()
        self.point = CFVec3A()

    def read(self, reader: BinaryReader):
        self.normal.read(reader)
        self.point.read(reader)

class FVisCell_t:
    def __init__(self):
        self.bounding_sphere_ws = CFSphere()
        self.parent_volume_idx = 0
        self.bounding_planes: list[FVisPlane_t] = []

    def read(self, reader: BinaryReader):
        self.bounding_sphere_ws.read(reader)
        self.parent_volume_idx = reader.read_U16()
        plane_count = reader.read_U8()
        reader.skip(1) # Padding
        planes_ptr = reader.read_U32()
        if planes_ptr != 0:
            with reader.detour(planes_ptr):
                self.bounding_planes = []
                for _ in range(plane_count):
                    plane = FVisPlane_t()
                    plane.read(reader)
                    self.bounding_planes.append(plane)

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
        print(f"({self.light_id}) Light name: {self.name}, type: {self.type}, flags: {self.flags}")
        self.parent_bone_idx = reader.read_S8()
        self.intensity = reader.read_F32()
        self.motif.read(reader)
        self.influence.read(reader)
        self.mtx_orientation.read(reader)
        self.spot_inner_radians = reader.read_F32()
        self.spot_outer_radians = reader.read_F32()
        self.corona_scale = reader.read_F32()

class FVisData_t:
    def __init__(self):
        self.cell_tree = FVisCellTree_t()
        self.ambient_light_color = CFColorRGB()
        self.fog_motif = CFColorMotif()
        self.portals = []
        self.volumes = []
        self.cells = []
        self.lights = []

    def read(self, reader: BinaryReader):
        portal_count = reader.read_U16()
        cell_count = reader.read_U16()
        volume_count = reader.read_U16()
        light_count = reader.read_U16()

        self.cell_tree.read(reader)
        self.ambient_light_color.read(reader)
        self.ambient_light_intensity = reader.read_F32()
        self.fog_start_z = reader.read_F32()
        self.fog_end_z = reader.read_F32()
        self.fog_motif.read(reader)

        self.portals = [FVisPortal_t() for _ in range(portal_count)]
        reader.read_ptr_objects(self.portals)

        self.volumes = [FVisVolume_t() for _ in range(volume_count)]
        reader.read_ptr_objects(self.volumes)

        self.cells = [FVisCell_t() for _ in range(cell_count)]
        reader.read_ptr_objects(self.cells)

        self.lights = [FLightInit_t() for _ in range(light_count)]
        reader.read_ptr_objects(self.lights)

class CFWorldShapeInit:
    """		FWorldShapeType_e m_nShapeType;	// The shape type code

		union 
		{							// Pointer to the type-specific shape object:
			void						*m_pShape;
			CFWorldShapeLine			*m_pLine;
			CFWorldShapeSpline			*m_pSpline;
			CFWorldShapeBox				*m_pBox;
			CFWorldShapeSphere			*m_pSphere;
			CFWorldShapeCylinder		*m_pCylinder;
			CFWorldShapeMesh			*m_pMesh;
		};

		CFMtx43 m_Mtx43;				// Orientation of the shape (Mesh shapes may have non-unit scale, but all other shapes will ALWAYS have m_Mtx43 unit scale)
		s32 m_nParentShapeIndex;		// The index of the CFWorldShapeInit in the init table that this shape is attached to (-1=not attached)
		void *m_pGameData;				// Pointer to game-specific data (NULL=none)

        """
    
    def __init__(self):
        self.type: WorldShapeType = WorldShapeType.COUNT
        self.shape: CFWorldShapeLine | CFWorldShapeSpline | CFWorldShapeBox | CFWorldShapeSphere | CFWorldShapeCylinder | CFWorldShapeMesh | None = None
        self.mtx = CFMtx43()
        self.parent_shape_index = -1
        self.game_data: FDataGamFile_Header_t | None = None

    def read(self, reader: BinaryReader):
        self.type = WorldShapeType(reader.read_U32())

        if self.type == WorldShapeType.LINE:
            self.shape = CFWorldShapeLine()
        elif self.type == WorldShapeType.SPLINE:
            self.shape = CFWorldShapeSpline()
        elif self.type == WorldShapeType.BOX:
            self.shape = CFWorldShapeBox()
        elif self.type == WorldShapeType.SPHERE:
            self.shape = CFWorldShapeSphere()
        elif self.type == WorldShapeType.CYLINDER:
            self.shape = CFWorldShapeCylinder()
        elif self.type == WorldShapeType.MESH:
            self.shape = CFWorldShapeMesh()
        elif self.type == WorldShapeType.POINT:
            self.shape = None
        else:
            raise Exception(f"Invalid shape type: {self.type}")

        if self.shape is None:
            reader.skip(4) # Skip shape pointer
        else:
            reader.read_ptr_object(self.shape)

        self.mtx.read(reader)
        self.parent_shape_index = reader.read_S32()

        self.game_data = None
        game_data_ptr = reader.read_U32()
        if game_data_ptr != 0:
            self.game_data = FDataGamFile_Header_t()
            with reader.detour(game_data_ptr, True):
                self.game_data.read(reader)

class FData_WorldInitHeader_t:
    def __init__(self):
        self.num_init_structs = 0

    def read(self, reader: BinaryReader):
        self.num_init_structs = reader.read_U32()
        reader.skip(12)

class CFWorldShapeLine:
    def __init__(self):
        self.length = 0.0

    def read(self, reader: BinaryReader):
        self.length = reader.read_F32()

class CFWorldShapeSpline:
    def __init__(self):
        self.closed = False
        self.points: list[CFVec3] = []

    def read(self, reader: BinaryReader):
        point_count = reader.read_U32()
        self.closed = reader.read_BOOL()

        self.points = [CFVec3() for _ in range(point_count)]
        reader.read_ptr_objects(self.points)

class CFWorldShapeBox:
    def __init__(self):
        self.dim_x = 0.0
        self.dim_y = 0.0
        self.dim_z = 0.0

    def read(self, reader: BinaryReader):
        self.dim_x = reader.read_F32()
        self.dim_y = reader.read_F32()
        self.dim_z = reader.read_F32()

class CFWorldShapeSphere:
    def __init__(self):
        self.radius = 0.0

    def read(self, reader: BinaryReader):
        self.radius = reader.read_F32()

class CFWorldShapeCylinder:
    def __init__(self):
        self.radius = 0.0
        self.dim_y = 0.0

    def read(self, reader: BinaryReader):
        self.radius = reader.read_F32()
        self.dim_y = reader.read_F32()

class CFWorldShapeMesh:
    def __init__(self):
        self.mesh_name: str = None
        self.lightmap_name: list[str] = []
        self.lightmap_motifs: list[int] = []
        self.mesh_inst_flags = 0
        self.cull_dist_2 = 0.0
        self.tint_rgb = CFColorRGB()
        self.color_streams = []
            
    def read(self, reader: BinaryReader):
        with reader.detour(reader.read_U32()):
            self.mesh_name = reader.read_string()

        self.lightmap_name = []
        for _ in range(4):
            with reader.detour(reader.read_U32()):
                name = reader.read_string()
                self.lightmap_name.append(name)

        self.lightmap_motifs = reader.read_U16s(4)
        self.mesh_inst_flags = reader.read_U32()
        self.cull_dist_2 = reader.read_F32()
        self.tint_rgb.read(reader)

        color_stream_count = reader.read_U8()
        reader.skip(3) # Padding

        self.color_streams = [ColorStream_t() for _ in range(color_stream_count)]
        reader.read_ptr_objects(self.color_streams)

class ColorStream_t:
    def __init__(self):
        self.vb_index = 0
        self.color_count = 0

    def read(self, reader: BinaryReader):
        self.vb_index = reader.read_U16()
        self.color_count = reader.read_U16()
        reader.read_U32() # TODO: Read color data from this ptr