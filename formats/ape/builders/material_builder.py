import math
import os
import bpy
import mathutils
from ....common.star_command_assembler import StarCommandAssembler
from ...common.types.common import CFColorMotif
from ..types.model import Ape, FMeshMaterial_t, MtlFlags
from ..types.texture import FShTexInst_t, TexLayerIdFlags
from ..dx8_shaders import SurfaceShaderRegisterType, LightShaderRegisterType, get_tool_shader_from_shader_combination
from .. import dx8_shaders

def build(ape: Ape, material: FMeshMaterial_t):
    surface_shader_info = dx8_shaders.get_surface_shader_reg_info(material.surface_shader)
    light_shader_info = dx8_shaders.get_light_shader_reg_info(material.light_shader)
    tool_shader = get_tool_shader_from_shader_combination(material.surface_shader, material.light_shader, material.specular_shader)
    
    print(f"Building material with surface shader {material.surface_shader} ({tool_shader}), light shader {material.light_shader}, specular shader {material.specular_shader}")
    print(f"   Material tint: {material.material_tint}")
    print(f"   Flags: {material.mtl_flags}")
    print(f"   Tool shader: {tool_shader.value} ({tool_shader})")
    print(f"   Surface registers for shader {material.surface_shader}")
    for i, reg in enumerate(material.surface_registers):
        type = surface_shader_info.register_types[i]
        print(f"  ({i}) {type}: {reg}")
        if isinstance(reg, FShTexInst_t):
            print(f"       Texture name: {reg.texture_name}")

    print(f"   Light registers for shader {material.light_shader}:")
    for i, reg in enumerate(material.light_registers):
        type = light_shader_info.register_types[i]
        print(f"  ({i}) {type}: {reg}")
        if isinstance(reg, FShTexInst_t):
            print(f"       Texture name: {reg.texture_name}")

    
    star_command_assembler = StarCommandAssembler()
    star_command_assembler.push("shader", tool_shader.value)
    _add_flag_star_commands(material, star_command_assembler)
    _add_tex_layer_commands(ape, material, star_command_assembler)

    layer0_register: FShTexInst_t = material.get_register(SurfaceShaderRegisterType.LAYER0)
    name = layer0_register.texture_name if layer0_register is not None else "material"
    name = f"{name}{star_command_assembler.assemble()}"

    mat = _build_blender_material(material, name)
    return mat

def build_textures_from_file_system(apes: Ape | list[Ape], texture_folder_path: str, recurse: bool = False):
    if not isinstance(apes, list):
        apes = [apes]

    texture_names = set()
    for ape in apes:
        _collect_texture_names_used_in_ape(ape, texture_names)

    for img in bpy.data.images:
        if img.name in texture_names:
            print(f"Texture {img.name} already loaded, skipping")
            texture_names.remove(img.name)

    if len(texture_names) == 0:
        return
    
    for root, _, files in os.walk(texture_folder_path):
        for file in files:
            base_file_name = os.path.basename(file)
            file_name, extension = os.path.splitext(base_file_name)
            file_name = file_name.lower()
            extension = extension.lower()
            if extension not in [".tga", ".png", ".jpg", ".jpeg"]:
                continue
            if file_name in texture_names:
                file_path = os.path.join(root, file)
                print(f"Loading texture {file_name} from {file_path}")

                img = bpy.data.images.load(file_path)
                img.name = file_name + ".tga"

                texture_names.remove(file_name)
                if len(texture_names) == 0:
                    return
        if not recurse:
            break

def _collect_texture_names_used_in_ape(ape: Ape, texture_names: set[str]):
    for material in ape.materials:
        surface_shader_info = dx8_shaders.get_surface_shader_reg_info(material.surface_shader)
        for i in range(surface_shader_info.tex_layer_count):
            register_type = SurfaceShaderRegisterType.layer(i)
            register: FShTexInst_t = material.get_register(register_type)
            if register is not None:
                texture_names.add(register.texture_name.lower())

def _build_principled_bsdf_material(material: FMeshMaterial_t, name: str):
    surface_shader_info = dx8_shaders.get_surface_shader_reg_info(material.surface_shader)
    
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    principled_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf.location = (400, 0)

    for i in range(surface_shader_info.tex_layer_count):
        register_type = SurfaceShaderRegisterType.layer(i)
        register: FShTexInst_t = material.get_register(register_type)
        if register is not None:
            tex_node = _build_texture_node(register, mat, i)
            if i == 0:
                links.new(tex_node.outputs["Color"], principled_bsdf.inputs["Base Color"])

    links.new(principled_bsdf.outputs[0], output.inputs["Surface"])

    return mat

def _build_blender_material(material: FMeshMaterial_t, name: str):
    shader = bpy.data.node_groups.get("FANG Material")
    if shader is None:
        return _build_principled_bsdf_material(material, name)
    
    surface_shader_info = dx8_shaders.get_surface_shader_reg_info(material.surface_shader)
    light_shader_info = dx8_shaders.get_light_shader_reg_info(material.light_shader)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    fang_shadergroup = nodes.new("ShaderNodeGroup")
    fang_shadergroup.node_tree = shader
    fang_shadergroup.location = (400, 0)

    links.new(fang_shadergroup.outputs[0], output.inputs["Surface"])

    emissive_register: CFColorMotif = material.get_register(LightShaderRegisterType.EMOTIF)
    if emissive_register is not None:
        fang_shadergroup.inputs["Emissive"].default_value = emissive_register.r

    emissive_mask: FShTexInst_t = material.get_register(LightShaderRegisterType.EMASK)
    if emissive_mask is not None:
        tex_node = _build_texture_node(emissive_mask, mat, 3)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Emissive Mask"])

    bumpmap: FShTexInst_t = material.get_register(LightShaderRegisterType.BUMPMAP)
    if bumpmap is not None:
        tex_node = _build_texture_node(bumpmap, mat, 4)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Bump Map"])

    detailmap = material.get_register(SurfaceShaderRegisterType.DETAILMAP)
    if detailmap is not None:
        tex_node = _build_texture_node(detailmap, mat, 5)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Detail Map"])

    tint = mathutils.Color((material.material_tint.r, material.material_tint.g, material.material_tint.b))
    tint = tint.from_srgb_to_scene_linear()
    fang_shadergroup.inputs["Tint Color"].default_value = (tint.r, tint.g, tint.b, 1.0)

    for i in range(surface_shader_info.tex_layer_count):
        register_type = SurfaceShaderRegisterType.layer(i)
        register: FShTexInst_t = material.get_register(register_type)
        if register is not None:
            tex_node = _build_texture_node(register, mat, i)
            if i == 0:
                links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Diffuse Color"])

    return mat

def _add_tex_layer_commands(ape: Ape, material: FMeshMaterial_t, star_commands: StarCommandAssembler):
    surface_shader_info = dx8_shaders.get_surface_shader_reg_info(material.surface_shader)

    tex_layer_id = None
    tex_layer_id_register_layer = None
    for i in range(surface_shader_info.tex_layer_count):
        register_type = SurfaceShaderRegisterType.layer(i)
        register: FShTexInst_t = material.get_register(register_type)
        if register is not None and register.tex_layer_id != 255:
            assert tex_layer_id is None or tex_layer_id == register.tex_layer_id
            tex_layer_id = register.tex_layer_id
            tex_layer_id_register_layer = i

    if tex_layer_id is None:
        return
    
    star_commands.push("id", tex_layer_id)
    tex_layer = None
    for layer in ape.tex_layer_id_array:
        if layer.tex_layer_id == tex_layer_id:
            tex_layer = layer
            break

    assert tex_layer is not None

    if tex_layer.flags & TexLayerIdFlags.BEGIN_SCROLLING:
        star_commands.push("scroll", tex_layer.scroll_st_per_sec.x, 1.0, tex_layer.scroll_st_per_sec.y, 1.0)
    if tex_layer.flags & TexLayerIdFlags.BEGIN_ROTATING:
        star_commands.push("rotate", tex_layer.uv_degree_rotation_per_sec, tex_layer.uv_rot_anchor[0], tex_layer.uv_rot_anchor[1])
    if tex_layer.flags & TexLayerIdFlags.BEGIN_FLIPPING:
        frames_per_sec = 0.0 if (tex_layer.frames_per_flip == 0) else (60.0 / tex_layer.frames_per_flip)
        star_commands.push("anim", tex_layer.flip_page_count, frames_per_sec)

def _add_flag_star_commands(material: FMeshMaterial_t, star_commands: StarCommandAssembler):
    affect_angle = math.acos(material.affect_angle) * 2.0 * (180.0 / math.pi)
    if material.mtl_flags & MtlFlags.NOCOLLIDE:
        star_commands.push("nocoll")
    #if material.mtl_flags & material.mtl_flags.RENDER_LAST: # TODO: This is set when *order was used, need to figure out what parameter is needed to be set
    #    star_commands.push("order", ???)
    if material.mtl_flags & MtlFlags.ZWRITE_ON:
        star_commands.push("writez")
    if material.mtl_flags & MtlFlags.DO_NOT_TINT:
        star_commands.push("nomeshtint")
    if material.mtl_flags & MtlFlags.DO_NOT_CAST_SHADOWS:
        star_commands.push("noshadows")
    if material.mtl_flags & MtlFlags.INVERT_EMISSIVE_MASK:
        star_commands.push("angtrans")
    if material.mtl_flags & MtlFlags.NO_ALPHA_SCROLL:
        star_commands.push("noascroll")
    if material.mtl_flags & MtlFlags.ANGULAR_EMISSIVE:
        star_commands.push("eangle", affect_angle)
    if material.mtl_flags & MtlFlags.ANGULAR_TRANSLUCENCY:
        star_commands.push("tangle", affect_angle)

def _find_image(texture_name: str):
    texture_name = texture_name.lower()
    for img in bpy.data.images:
        if img.name.lower() == texture_name:
            return img

def _build_texture_node(texture: FShTexInst_t, mat: bpy.types.Material, offset: int = 0):
    tex_name = f"{texture.texture_name}.tga"
    img = _find_image(tex_name)
    if img is None:
        img = bpy.data.images.new(tex_name, 1, 1)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = (0, offset * -300)
    return tex