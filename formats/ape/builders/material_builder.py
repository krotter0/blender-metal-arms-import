import os
import bpy
from mathutils import Color
from ..parsers.models.material import ParsedMotif, ParsedMotif, ParsedTextureInstance, ParsedMaterial
from ....common.star_command_assembler import StarCommandAssembler
from ..types.shaders import SurfaceShaderRegisterType, LightShaderRegisterType

def build(material: ParsedMaterial) -> bpy.types.Material:
    star_command_assembler = StarCommandAssembler()
    star_command_assembler.push("shader", material.shader.value)
    for star_command in material.star_commands:
        star_command_assembler.push(star_command)

    layer0_register: ParsedTextureInstance = material.get_register_value(SurfaceShaderRegisterType.LAYER0)
    name = layer0_register.texture_name if layer0_register is not None else "material"
    name = f"{name}{star_command_assembler.assemble()}"

    return _build_blender_material(material, name)

def build_textures_from_file_system(materials: list[ParsedMaterial], texture_folder_path: str, recurse: bool = False, allowed_extensions: list[str] = [".tga", ".png", ".jpg", ".jpeg"]):
    if not isinstance(materials, list):
        materials = [materials]

    texture_names = set()
    for material in materials:
        _collect_texture_names_used_in_material(material, texture_names)

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
            if extension not in allowed_extensions:
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

def _collect_texture_names_used_in_material(material: ParsedMaterial, texture_names: set[str]):
    for register in material.surface_registers.values():
        if isinstance(register.value, ParsedTextureInstance):
            texture_names.add(register.value.texture_name.lower())

def _build_principled_bsdf_material(material: ParsedMaterial, name: str):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    principled_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf.location = (400, 0)

    for i in range(material.tex_layer_count):
        register_type = SurfaceShaderRegisterType.layer(i)
        register: ParsedTextureInstance = material.get_register_value(register_type)
        if register is not None:
            tex_node = _build_texture_node(register, mat, i)
            if i == 0:
                links.new(tex_node.outputs["Color"], principled_bsdf.inputs["Base Color"])

    links.new(principled_bsdf.outputs[0], output.inputs["Surface"])

    return mat

def _build_blender_material(material: ParsedMaterial, name: str):
    shader = bpy.data.node_groups.get("FANG Material")
    if shader is None:
        return _build_principled_bsdf_material(material, name)

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

    emissive_register: ParsedMotif = material.get_register_value(LightShaderRegisterType.EMOTIF)
    if emissive_register is not None:
        fang_shadergroup.inputs["Emissive"].default_value = emissive_register.motif_color[0]

    emissive_mask: ParsedTextureInstance = material.get_register_value(LightShaderRegisterType.EMASK)
    if emissive_mask is not None:
        tex_node = _build_texture_node(emissive_mask, mat, 3)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Emissive Mask"])

    bumpmap: ParsedTextureInstance = material.get_register_value(LightShaderRegisterType.BUMPMAP)
    if bumpmap is not None:
        tex_node = _build_texture_node(bumpmap, mat, 4)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Bump Map"])

    detailmap: ParsedTextureInstance = material.get_register_value(SurfaceShaderRegisterType.DETAILMAP)
    if detailmap is not None:
        tex_node = _build_texture_node(detailmap, mat, 5)
        links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Detail Map"])

    tint = Color(material.tint)
    tint = tint.from_srgb_to_scene_linear()
    fang_shadergroup.inputs["Tint Color"].default_value = (tint.r, tint.g, tint.b, 1.0)

    for i in range(material.tex_layer_count):
        register_type = SurfaceShaderRegisterType.layer(i)
        register: ParsedTextureInstance = material.get_register_value(register_type)
        if register is not None:
            tex_node = _build_texture_node(register, mat, i)
            if i == 0:
                links.new(tex_node.outputs["Color"], fang_shadergroup.inputs["Diffuse Color"])

    return mat

def _find_image(texture_name: str):
    texture_name = texture_name.lower()
    for img in bpy.data.images:
        if img.name.lower() == texture_name:
            return img

def _build_texture_node(texture: ParsedTextureInstance, mat: bpy.types.Material, offset: int = 0):
    tex_name = f"{texture.texture_name}.tga"
    img = _find_image(tex_name)
    if img is None:
        img = bpy.data.images.new(tex_name, 1, 1)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = (0, offset * -300)
    return tex