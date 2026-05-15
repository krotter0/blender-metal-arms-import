from enum import Flag
from ....common.platform import Platform
from ...common.types.common import CFSphere, CFColorRGB, CFVec3
from ....common.binary_reader import BinaryReader
from ...common.types.lights import FLightInit_t
from .texture import FMeshTexLayerID_t
from ..types.skeleton import FMeshBone_t
from .model_dx8 import FDX8MeshMaterial_t, FDX8Mesh_t
from .model_gc import FGCMesh_t, FGCMeshMaterial_t
from . import shaders

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

class FMeshMaterial_t:
    def __init__(self, platform: Platform):
        self.platform = platform
        self.light_shader: shaders.LightShader = None
        self.specular_shader: shaders.SpecularShader = None
        self.surface_shader: shaders.SurfaceShader = None
        self.part_id_mask = 0
        if self.platform == Platform.DX:
            self.platform_data = FDX8MeshMaterial_t()
        elif self.platform == Platform.GC:
            self.platform_data = FGCMeshMaterial_t()
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
            self.light_shader = shaders.LightShader.parse(light_shader_idx, self.platform)

        if specular_shader_idx == 0xFF:
            self.specular_shader = None
        else:
            self.specular_shader = shaders.SpecularShader.parse(specular_shader_idx, self.platform)

        if surface_shader_idx == 0xFFFF:
            self.surface_shader = None
        else:
            self.surface_shader = shaders.SurfaceShader.parse(surface_shader_idx, self.platform)
        
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
        
        surface_register_info = shaders.get_surface_shader_reg_info(self.surface_shader)
        self.surface_registers = self._read_registers(reader, surface_registers_ptr, surface_register_info.register_types)

        light_register_info = shaders.get_light_shader_reg_info(self.light_shader)
        self.light_registers = self._read_registers(reader, light_registers_ptr, light_register_info.register_types)

    def get_register(self, register_type: shaders.SurfaceShaderRegisterType | shaders.LightShaderRegisterType):
        if isinstance(register_type, shaders.SurfaceShaderRegisterType):
            register_info = shaders.get_surface_shader_reg_info(self.surface_shader)
            registers = self.surface_registers
        elif isinstance(register_type, shaders.LightShaderRegisterType):
            register_info = shaders.get_light_shader_reg_info(self.light_shader)
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

    def _read_register_data(self, reader: BinaryReader, register_type: shaders.SurfaceShaderRegisterType | shaders.LightShaderRegisterType):
        data_type = shaders.get_shader_reg_datatype(register_type)
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

class Ape:
    def __init__(self, platform: Platform):
        self.platform = platform
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
        
        if self.platform == Platform.DX:
            self.mesh_is = FDX8Mesh_t()
        elif self.platform == Platform.GC:
            self.mesh_is = FGCMesh_t()
        
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
        bone_stride = 320 if self.platform == Platform.DX else None
        reader.read_ptr_objects(self.bones, bone_stride)
        
        self.lights = [FLightInit_t() for _ in range(light_count)]
        reader.read_ptr_objects(self.lights)
        
        skeleton_index_array_ptr = reader.read_U32()
        with reader.detour(skeleton_index_array_ptr):
            self.skeletonIndexArray = reader.read_U8s(bone_count)
        
        self.materials = [FMeshMaterial_t(self.platform) for _ in range(material_count)]
        reader.read_ptr_objects(self.materials)
        
        coll_tree_ptr = reader.read_U32()
        
        self.tex_layer_id_array = [FMeshTexLayerID_t() for _ in range(self.tex_layer_id_count)]
        reader.read_ptr_objects(self.tex_layer_id_array)
        
        reader.read_ptr_object(self.mesh_is)