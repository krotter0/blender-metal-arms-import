from enum import Flag
from ...common.types.common import CFSphere, CFColorRGB, CFVec3
from ....common.binary_reader import BinaryReader
from ...common.types.lights import FLightInit_t
from .texture import FMeshTexLayerID_t
from ..types.skeleton import FMeshBone_t

from .. import dx8_shaders

class MtlFlags(Flag):
    NONE = 0x0000
    NOCOLLIDE = 0x0001
    RENDER_LAST = 0x0002
    ZWRITE_ON = 0x0004
    DO_NOT_TINT = 0x0008
    DO_NOT_CAST_SHADOWS = 0x0010
    INVERT_EMISSIVE_MASK = 0x0020
    ANGULAR_EMISSIVE = 0x0040
    ANGULAR_TRANSLUCENCY = 0x0080
    NO_ALPHA_SCROLL = 0x0100

class Vertex:
    def __init__(self):
        self.pos: tuple[float, float, float] = None
        self.normals: list[tuple[float, float, float]] = None
        self.weights: list[float] = None
        self.colors: list[tuple[float, float, float, float]] = None
        self.uvs: list[tuple[float, float]] = None

    def read(self, reader: BinaryReader, vertex_format: dx8_shaders.FDX8VB_Info):
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

    def _read_tcs(self, reader: BinaryReader, vertex_format: dx8_shaders.FDX8VB_Info):
        return [reader.read_F32s(2) for _ in range(vertex_format.tc_count)]
    
    def _read_colors(self, reader: BinaryReader, vertex_format: dx8_shaders.FDX8VB_Info):
        colors = []
        for _ in range(vertex_format.color_count):
            r = reader.read_U8() / 255.0
            g = reader.read_U8() / 255.0
            b = reader.read_U8() / 255.0
            a = reader.read_U8() / 255.0
            colors.append((r, g, b, a))
        return colors
    
    def _read_weights(self, reader: BinaryReader, vertex_format: dx8_shaders.FDX8VB_Info):
        return [reader.read_F32() for _ in range(vertex_format.weight_count)]
    
    def _read_normals(self, reader: BinaryReader, vertex_format: dx8_shaders.FDX8VB_Info):
        return [reader.read_F32s(3) for _ in range(vertex_format.normal_count)]
    
    def _read_pos(self, reader: BinaryReader):
        return reader.read_F32s(3)


class FMeshSeg_t:
    def __init__(self):
        self.bound_sphere_ms = CFSphere()
        self.bone_mtx_count = 0
        self.bone_mtx_indices: list[int] = []

    def read(self, reader: BinaryReader):
        self.bound_sphere_ms.read(reader)
        self.bone_mtx_count = reader.read_U8()
        if self.bone_mtx_count > 1:
            raise NotImplementedError("Only segments with 0-1 bones are supported for now")
        self.bone_mtx_indices = reader.read_U8s(self.bone_mtx_count)
        reader.skip(4 - self.bone_mtx_count) # bone_mtx_indices is originally a fixed array of length 4, but only bone_mtx_count entries are valid

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
        self.info: dx8_shaders.FDX8VB_Info = None
        self.dynamic = False
        self.software_vp = False
        self.locked = False
        self.lock_buf = 0
        self.lock_offset = 0
        self.lock_bytes = 0
        self.vertex_shader = 0
        self.vb: list[Vertex] = []

    def read(self, reader: BinaryReader):
        reader.skip(8) #FLink_t
        vtx_count = reader.read_U32()
        bytes_per_vertex = reader.read_U16()
        
        self.lmtc_count = reader.read_U16()
        self.lmuv_stream = reader.read_U32()
        self.basis = [FDX8BasisVectors_t() for _ in range(vtx_count)]
        reader.read_ptr_objects(self.basis)
        
        info_index = reader.read_S8()
        self.info = dx8_shaders.FDX8VB_InfoTable[info_index]
        self.dynamic = reader.read_BOOL8()
        self.software_vp = reader.read_BOOL8()
        
        self.locked = reader.read_BOOL8()
        self.lock_buf = reader.read_U32()
        
        self.lock_offset = reader.read_U32()
        self.lock_bytes = reader.read_U32()
        
        self.vertex_shader = reader.read_U32()
        
        dxvb = reader.read_U32()
        with reader.detour(dxvb):
            self.vb = [Vertex() for _ in range(vtx_count)]
            for i in range(vtx_count):
                self.vb[i].read(reader, self.info)

class FMeshMaterial_t:
    def __init__(self):
        self.light_shader: dx8_shaders.LightShader = None
        self.specular_shader: dx8_shaders.SpecularShader = None
        self.surface_shader: dx8_shaders.SurfaceShader = None
        self.part_id_mask = 0
        self.platform_data = FDX8MeshMaterial_t()
        self.lod_mask = 0
        self.depth_bias_level = 0
        self.base_st_sets = 0
        self.lightmap_st_sets = 0
        self.tex_layer_id_index = [0, 0, 0, 0]
        self.affect_angle = 0.0
        self.affect_normal = (0.0, 0.0, 0.0)
        self.affect_bone_id = 0
        self.unit_radius = 0.0
        self.mtl_flags: MtlFlags = MtlFlags.NONE
        self.draw_key = 0
        self.material_tint = CFColorRGB()
        self.average_vert_pos = CFVec3()
        self.hash_key = 0

    def read(self, reader: BinaryReader):
        light_registers_ptr = reader.read_U32()
        surface_registers_ptr = reader.read_U32()

        light_shader_idx = reader.read_U8()
        specular_shader_idx = reader.read_U8()
        surface_shader_idx = reader.read_U16()
        if light_shader_idx == 0xFF:
            self.light_shader = None
        else:
            self.light_shader = dx8_shaders.LightShader(light_shader_idx)

        if specular_shader_idx == 0xFF:
            self.specular_shader = None
        else:
            self.specular_shader = dx8_shaders.SpecularShader(specular_shader_idx)

        if surface_shader_idx == 0xFFFF:
            self.surface_shader = None
        else:
            self.surface_shader = dx8_shaders.SurfaceShader(surface_shader_idx)
        
        self.part_id_mask = reader.read_U32()
        
        reader.read_ptr_object(self.platform_data)
        
        self.lod_mask = reader.read_U8()
        self.depth_bias_level = reader.read_U8()
        self.base_st_sets = reader.read_U8()
        self.lightmap_st_sets = reader.read_U8()
        self.tex_layer_id_index = reader.read_U8s(4)
        self.affect_angle = reader.read_F32()
        
        comp_affect_normal = reader.read_S8s(3)
        self.affect_normal = (comp_affect_normal[0] / 64.0, comp_affect_normal[1] / 64.0, comp_affect_normal[2] / 64.0)
        self.affect_bone_id = reader.read_S8()
        
        compressed_radius = reader.read_U8()
        self.unit_radius = compressed_radius / 255.0
        
        reader.read_U8() #pad
        
        self.mtl_flags = MtlFlags(reader.read_U16())
        self.draw_key = reader.read_U32()
        
        self.material_tint.read(reader)
        self.average_vert_pos.read(reader)
        
        self.hash_key = reader.read_U32() #missing from old versions?
        
        surface_register_info = dx8_shaders.get_surface_shader_reg_info(self.surface_shader)
        self.surface_registers = self._read_registers(reader, surface_registers_ptr, surface_register_info.register_types)

        light_register_info = dx8_shaders.get_light_shader_reg_info(self.light_shader)
        self.light_registers = self._read_registers(reader, light_registers_ptr, light_register_info.register_types)

    def get_register(self, register_type: dx8_shaders.SurfaceShaderRegisterType | dx8_shaders.LightShaderRegisterType):
        if isinstance(register_type, dx8_shaders.SurfaceShaderRegisterType):
            register_info = dx8_shaders.get_surface_shader_reg_info(self.surface_shader)
            registers = self.surface_registers
        elif isinstance(register_type, dx8_shaders.LightShaderRegisterType):
            register_info = dx8_shaders.get_light_shader_reg_info(self.light_shader)
            registers = self.light_registers
        else:
            raise ValueError(f"Invalid parameter given for register_type")
        
        for i, reg in enumerate(registers):
            if reg is not None and register_info.register_types[i] == register_type:
                return reg

    def _read_registers(self, reader: BinaryReader, registers_ptr: int, register_types: list):
        registers = []
        with reader.detour(registers_ptr):
            register_count = len(register_types)
            for i in range(register_count):
                reg_data = self._read_register_data(reader, register_types[i])
                registers.append(reg_data)
        return registers

    def _read_register_data(self, reader: BinaryReader, register_type: dx8_shaders.SurfaceShaderRegisterType | dx8_shaders.LightShaderRegisterType):
        data_type = dx8_shaders.get_shader_reg_datatype(register_type)
        if data_type == int:
            reg_data = reader.read_U32()
        elif data_type == float:
            reg_data = reader.read_F32()
        else:
            register_ptr = reader.read_U32()
            if register_ptr == 0:
                return None
            with reader.detour(register_ptr):
                reg_data = data_type()
                reg_data.read(reader)
        return reg_data

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

class FDX8Mesh_s:
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

class Ape:
    def __init__(self):
        self.name = ""
        self.bound_sphere_ms = CFSphere()
        self.bound_box_min_ms = CFVec3()
        self.bound_box_max_ms = CFVec3()

        self.flags: int = 0
        self.mesh_coll_mask: int = 0
        self.used_bone_count: int = 0
        self.root_bone_index: int = 0
        self.tex_layer_id_count: int = 0
        self.tex_layer_id_count_st: int = 0
        self.tex_layer_id_count_flip: int = 0
        self.coll_tree_count: int = 0
        self.lod_count: int = 0
        self.shadow_lod_bias: int = 0
        self.lod_distances: list[float] = []
        self.segs: list[FMeshSeg_t] = []
        self.bones: list[FMeshBone_t] = []
        self.lights: list[FLightInit_t] = []
        self.materials: list[FMeshMaterial_t] = []
        self.tex_layer_id_array: list[FMeshTexLayerID_t] = []
        
        self.mesh_is = FDX8Mesh_s()
        
    def read(self, reader: BinaryReader):
        self.name = reader.read_string(16)
        self.bound_sphere_ms.read(reader)
        self.bound_box_min_ms.read(reader)
        self.bound_box_max_ms.read(reader)
        self.flags = reader.read_U16()
        self.mesh_coll_mask = reader.read_U16()
        self.used_bone_count = reader.read_U8()
        self.root_bone_index = reader.read_U8()
        bone_count = reader.read_U8()
        seg_count = reader.read_U8()
        self.tex_layer_id_count = reader.read_U8()
        self.tex_layer_id_count_st = reader.read_U8()
        self.tex_layer_id_count_flip = reader.read_U8()
        light_count = reader.read_U8()
        material_count = reader.read_U8()
        self.coll_tree_count = reader.read_U8()
        self.lod_count = reader.read_U8()
        self.shadow_lod_bias = reader.read_U8()
        
        self.lod_distances = reader.read_F32s(8)
        
        self.segs = [FMeshSeg_t() for _ in range(seg_count)]
        reader.read_ptr_objects(self.segs, 24)
        
        self.bones = [FMeshBone_t() for _ in range(bone_count)]
        reader.read_ptr_objects(self.bones, 320)
        
        self.lights = [FLightInit_t() for _ in range(light_count)]
        reader.read_ptr_objects(self.lights)
        
        skeleton_index_array_ptr = reader.read_U32()
        with reader.detour(skeleton_index_array_ptr):
            self.skeletonIndexArray = reader.read_U8s(bone_count)
        
        self.materials = [FMeshMaterial_t() for _ in range(material_count)]
        reader.read_ptr_objects(self.materials)
        
        coll_tree_ptr = reader.read_U32()
        
        self.tex_layer_id_array = [FMeshTexLayerID_t() for _ in range(self.tex_layer_id_count)]
        reader.read_ptr_objects(self.tex_layer_id_array)
        
        reader.read_ptr_object(self.mesh_is)