import math
from ..types.texture import FShTexInst_t, TexLayerIdFlags

from .models.material import ParsedMaterial, ParsedShaderRegister, ParsedTextureInstance, ParsedMotif
from ..types.model import FMesh_t, FMeshMaterial_t, MtlFlags
from ..types.shaders import FLightShaderReg_t, FShaderReg_t, FShaderReg_t, LightShader, LightShaderRegisterType, SpecularShader, SurfaceShader, SurfaceShaderRegisterType, get_light_shader_reg_info, get_surface_shader_reg_info, get_shader_reg_datatype, get_tool_shader_from_shader_combination
from ....common.platform import Platform
from ....structs.genericfieldtypes import *
from ....structs.pointer import Pointer, PointerFieldType
from ...common.types.common import *
from ....common.star_command_assembler import StarCommand

class MaterialParser:
    def __init__(self, platform: Platform):
        self._platform = platform
        self._light_shader_registers: dict[LightShaderRegisterType, ParsedShaderRegister] = {}
        self._surface_shader_registers: dict[SurfaceShaderRegisterType, ParsedShaderRegister] = {}
        self._surface_shader_info: FShaderReg_t = None
        self._light_shader_info: FLightShaderReg_t = None

    def _get_surface_register(self, register_type: SurfaceShaderRegisterType):
        return self._surface_shader_registers.get(register_type, None)

    def _get_light_register(self, register_type: LightShaderRegisterType):
        return self._light_shader_registers.get(register_type, None)

    def _get_tex_layer_star_commands(self, model: FMesh_t):
        tex_layer_id = None
        tex_layer_id_register_layer = None
        for i in range(self._surface_shader_info.tex_layer_count):
            register_type = SurfaceShaderRegisterType.layer(i)
            register: ParsedShaderRegister = self._get_surface_register(register_type)
            if register is not None:
                texture: ParsedTextureInstance = register.value
                if tex_layer_id is not None and texture.tex_layer_id != tex_layer_id:
                    print(f"Warning: Material has multiple different tex layer ids, skipping...") #TODO
                    return []
                tex_layer_id = texture.tex_layer_id
                tex_layer_id_register_layer = i

        if tex_layer_id is None or tex_layer_id == 255:
            return []
        
        star_commands: list[StarCommand] = []
        star_commands.append(StarCommand("id", tex_layer_id))
        tex_layer = None
        for layer in model.tex_layer_id_array:
            if layer.tex_layer_id == tex_layer_id:
                tex_layer = layer
                break

        assert tex_layer is not None

        if tex_layer.flags & TexLayerIdFlags.BEGIN_SCROLLING:
            star_commands.append(StarCommand("scroll", tex_layer.scroll_st_per_sec.x, 1.0, tex_layer.scroll_st_per_sec.y, 1.0))
        if tex_layer.flags & TexLayerIdFlags.BEGIN_ROTATING:
            star_commands.append(StarCommand("rotate", tex_layer.uv_degree_rotation_per_sec, tex_layer.uv_rot_anchor[0], tex_layer.uv_rot_anchor[1]))
        if tex_layer.flags & TexLayerIdFlags.BEGIN_FLIPPING:
            frames_per_sec = 0.0 if (tex_layer.frames_per_flip == 0) else (60.0 / tex_layer.frames_per_flip)
            star_commands.append(StarCommand("anim", tex_layer.flip_page_count, frames_per_sec))

        return star_commands

    def _get_flag_star_commands(self, material: FMeshMaterial_t):
        star_commands: list[StarCommand] = []
        affect_angle = math.acos(material.affect_angle) * 2.0 * (180.0 / math.pi)
        mtl_flags = material.mtl_flags
        if mtl_flags & MtlFlags.NOCOLLIDE:
            star_commands.append(StarCommand("nocoll"))
        #if mtl_flags & mtl_flags.RENDER_LAST: # TODO: This is set when *order was used, need to figure out what parameter is needed to be set
        #    star_commands.append("order", ???)
        if mtl_flags & MtlFlags.ZWRITE_ON:
            star_commands.append(StarCommand("writez"))
        if mtl_flags & MtlFlags.DO_NOT_TINT:
            star_commands.append(StarCommand("nomeshtint"))
        if mtl_flags & MtlFlags.DO_NOT_CAST_SHADOWS:
            star_commands.append(StarCommand("noshadows"))
        if mtl_flags & MtlFlags.INVERT_EMISSIVE_MASK:
            star_commands.append(StarCommand("angtrans"))
        if mtl_flags & MtlFlags.NO_ALPHA_SCROLL:
            star_commands.append(StarCommand("noascroll"))
        if mtl_flags & MtlFlags.ANGULAR_EMISSIVE:
            star_commands.append(StarCommand("eangle", affect_angle))
        if mtl_flags & MtlFlags.ANGULAR_TRANSLUCENCY:
            star_commands.append(StarCommand("tangle", affect_angle))
        return star_commands

    def _parse_star_commands(self, material: FMeshMaterial_t, model: FMesh_t):
        star_commands: list[StarCommand] = []
        star_commands.extend(self._get_flag_star_commands(material))
        star_commands.extend(self._get_tex_layer_star_commands(model))
        return star_commands

    def _parse_register_value(self, ptr: Pointer[None], reg_type: FieldType):
        if reg_type is None:
            raise ValueError("Register data type cannot be None")
        if ptr.address == 0:
            return None
        ptr = ptr.cast(reg_type)
        if not isinstance(reg_type, PointerFieldType):
            return ptr.deref
        
        sub_ptr: Pointer = ptr.deref
        if sub_ptr.address == 0:
            return None
        pointee_type = type(sub_ptr.pointee_type)
        if pointee_type == FShTexInst_t:
            tex: FShTexInst_t = sub_ptr.deref
            tex_name_ptr = sub_ptr.cast(NullTermString)
            tex_name_ptr.address = tex.texture_name_offset
            tex_name = tex_name_ptr.deref
            return ParsedTextureInstance(texture_name=tex_name, tex_layer_id=tex.tex_layer_id)
        elif pointee_type == CFColorMotif:
            motif: CFColorMotif = sub_ptr.deref
            return ParsedMotif(motif_color=(motif.r, motif.g, motif.b), motif_index=motif.motif_index)
        else:
            raise ValueError(f"Unsupported shader register data type: {sub_ptr.pointee_type}")

    def _parse_registers(self, registers_ptr: Pointer[None], register_types: list[LightShaderRegisterType | SurfaceShaderRegisterType]):
        registers: dict[LightShaderRegisterType | SurfaceShaderRegisterType, ParsedShaderRegister] = {}

        register_count = len(register_types)
        for i in range(register_count):
            register_type = register_types[i]
            register_data_type = get_shader_reg_datatype(register_type)

            register_ptr = registers_ptr + (i * 4)
            value = self._parse_register_value(register_ptr, register_data_type)
            parsed_register = ParsedShaderRegister(value=value)
            registers[register_type] = parsed_register

        return registers

    def parse(self, material: FMeshMaterial_t, model: FMesh_t) -> ParsedMaterial:
        light_shader = LightShader.parse(material.light_shader_idx, self._platform)
        surface_shader = SurfaceShader.parse(material.surface_shader_idx, self._platform)
        specular_shader = SpecularShader.parse(material.specular_shader_idx, self._platform) if material.specular_shader_idx != 255 else None
        
        shader = get_tool_shader_from_shader_combination(surface_shader, light_shader, specular_shader)

        self._light_shader_info = get_light_shader_reg_info(light_shader)
        self._surface_shader_info = get_surface_shader_reg_info(surface_shader)
        self._light_shader_registers = self._parse_registers(material.light_registers, self._light_shader_info.register_types)
        self._surface_shader_registers = self._parse_registers(material.surface_registers, self._surface_shader_info.register_types)

        star_commands = self._parse_star_commands(material, model)

        return ParsedMaterial(
            shader=shader,
            surface_registers=self._surface_shader_registers,
            light_registers=self._light_shader_registers,
            surface_shader=surface_shader,
            light_shader=light_shader,
            tex_layer_count=self._surface_shader_info.tex_layer_count,
            star_commands=star_commands,
            tint=(material.material_tint.r, material.material_tint.g, material.material_tint.b)
        )