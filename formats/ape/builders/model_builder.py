from dataclasses import dataclass

import bpy
from mathutils import Matrix, Vector

from ....common.platform import Platform
from . import material_builder, skeleton_builder
from ....formats.common.builders import light_builder
from ..parsers.model import *
from ..parsers.models.model import ParsedModel, ParsedMesh
from ..parsers.models.skeleton import ParsedSkeleton

@dataclass
class ModelBuildOptions:
    platform: Platform = None
    filepath: str = ""
    lod_index: int = None
    create_armature: bool = True
    merge_clusters: bool = False
    parent: bpy.types.Object = None
    name: str = None
    texture_folder_path: str = None
    texture_allow_recurse: bool = True
    texture_extension: str = ".png"
    hide_lods: bool = True
    apply_lod_name_prefix: bool = True
    import_lights: bool = True

def _build_uvs(mesh: bpy.types.Mesh, parsed_mesh: ParsedMesh):
    if parsed_mesh.uvs is None or parsed_mesh.uv_channels == 0:
        return
    
    uv_count = parsed_mesh.uv_channels
    for uv_index in range(uv_count):
        uv_layer = mesh.uv_layers.new(name=f"uv_{uv_index}")

        for poly in mesh.polygons:
            poly.use_smooth = True
            for loop_index in poly.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                vert_uvs = parsed_mesh.uvs[vertex_index]
                if uv_index < len(vert_uvs):
                    u = vert_uvs[uv_index][0]
                    v = vert_uvs[uv_index][1]
                    uv_layer.data[loop_index].uv = (u, v)

def _build_colors(mesh: bpy.types.Mesh, parsed_mesh: ParsedMesh):
    if not parsed_mesh.colors:
        return

    color_set_count = parsed_mesh.color_channels
    if color_set_count == 0:
        return
    
    for channel_index in range(color_set_count):
        color_attribute = mesh.color_attributes.new(name=f"color_{channel_index}", type='BYTE_COLOR', domain='POINT')
        colors = []
        for vertex_colors in parsed_mesh.colors:
            if channel_index < len(vertex_colors):
                colors.extend(vertex_colors[channel_index])
        color_attribute.data.foreach_set("color", colors)

def _build_normals(mesh: bpy.types.Mesh, parsed_mesh: ParsedMesh):
    if parsed_mesh.normals is None or len(parsed_mesh.normals) == 0:
        return
    
    loop_normals = [parsed_mesh.normals[loop.vertex_index][0] for loop in mesh.loops]
    mesh.normals_split_custom_set(loop_normals)

def _transform_vertices_with_bone_matrix(parsed_mesh: ParsedMesh, skeleton: ParsedSkeleton, mesh: bpy.types.Mesh):
    if parsed_mesh.bone_indices is None:
        return

    bone_matrices = [Matrix(bone.bone_to_model_matrix) for bone in skeleton.bones]

    for vertex_index, bone_index in enumerate(parsed_mesh.bone_indices):
        if bone_index is not None:
            bone_matrix = bone_matrices[bone_index]
            vertex = mesh.vertices[vertex_index]
            vertex.co = bone_matrix @ vertex.co

def _apply_materials(mesh: bpy.types.Mesh, parsed_mesh: ParsedMesh, materials: list[bpy.types.Material]):
    for i, polygon in enumerate(mesh.polygons):
        polygon.material_index = parsed_mesh.material_indices[i]

    for material in materials:
        mesh.materials.append(material)

def _build_skin_weights(parsed_mesh: ParsedMesh, skeleton: ParsedSkeleton, obj: bpy.types.Object, armature_object: bpy.types.Object):
    if parsed_mesh.bone_indices is None:
        return

    vertex_groups = {}
    for vertex_index, bone_index in enumerate(parsed_mesh.bone_indices):
        bone = skeleton.bones[bone_index]
        bone_name = bone.name
        if bone_index not in vertex_groups:
            vertex_groups[bone_index] = [vertex_index]
        else:
            vertex_groups[bone_index].append(vertex_index)

    for bone_index, vertex_indices in vertex_groups.items():
        bone_name = skeleton.bones[bone_index].name
        vg = obj.vertex_groups.new(name=bone_name)
        vg.add(vertex_indices, 1.0, 'REPLACE')

    arm_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
    arm_mod.object = armature_object

def _merge_prepass(parsed_model: ParsedModel):
    lod_meshes: dict[int, list[ParsedMesh]] = {}
    for mesh in parsed_model.meshes:
        if mesh.lod_id not in lod_meshes:
            lod_meshes[mesh.lod_id] = []
        lod_meshes[mesh.lod_id].append(mesh)

    merged_meshes = []
    for meshes in lod_meshes.values():
        merged_mesh = ParsedMesh.merge_meshes(meshes)
        merged_meshes.append(merged_mesh)
    return merged_meshes

def _build_mesh(parsed_model: ParsedModel, parsed_mesh: ParsedMesh, armature_object: bpy.types.Object = None, model_name: str | None=None, apply_lod_name_prefix: bool = True, materials: list[bpy.types.Material] = None):
    mesh_name = model_name
    if apply_lod_name_prefix:
        mesh_name = f"LOD{parsed_mesh.lod_id}_{mesh_name}"

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(list(parsed_mesh.verts), [], list(parsed_mesh.faces))
    mesh.update()

    if parsed_mesh.uvs != None:
        _build_uvs(mesh, parsed_mesh)
    if parsed_mesh.colors != None:
        _build_colors(mesh, parsed_mesh)
    if parsed_mesh.normals != None:
        _build_normals(mesh, parsed_mesh)
    if parsed_mesh.bone_indices is not None and parsed_model.skeleton is not None:
        _transform_vertices_with_bone_matrix(parsed_mesh, parsed_model.skeleton, mesh)

    if materials is not None:
        _apply_materials(mesh, parsed_mesh, materials)

    obj = bpy.data.objects.new(mesh_name, mesh)

    if armature_object is not None:
        _build_skin_weights(parsed_mesh, parsed_model.skeleton, obj, armature_object)

    collection = bpy.context.collection
    collection.objects.link(obj)
    return obj

def _hide_lod_meshes(parsed_meshes: list[ParsedMesh], mesh_objects: list[bpy.types.Object]):
    if len(parsed_meshes) <= 1:
        return
    lowest_lod = min(mesh.lod_id for mesh in parsed_meshes)
    for parsed_mesh, obj in zip(parsed_meshes, mesh_objects):
        if parsed_mesh.lod_id > lowest_lod:
            obj.hide_set(True)

def _build_lights(parsed_model: ParsedModel, parent: bpy.types.Object = None):
    if parsed_model.lights is None or len(parsed_model.lights) == 0:
        return
    
    for i, parsed_light in enumerate(parsed_model.lights):
        light = light_builder.build(i, parsed_light)
        if light is not None and parsed_model.skeleton is not None and parsed_light.parent_bone_idx != -1:
            bone = parsed_model.skeleton.bones[parsed_light.parent_bone_idx]

            bone_to_model_mtx = Matrix(bone.bone_to_model_matrix)
            
            light.location = bone_to_model_mtx @ Vector(light.location)
            light_rot_mtx = light.rotation_quaternion.to_matrix()
            light.rotation_quaternion = (bone_to_model_mtx.to_3x3() @ light_rot_mtx).to_quaternion()

            light.parent = parent
            if parent is not None and parent.type == "ARMATURE":
                light.parent_type = "BONE"
                light.parent_bone = bone.name

def _build_materials(parsed_model: ParsedModel):
    if parsed_model.materials is None or len(parsed_model.materials) == 0:
        return
    
    return [material_builder.build(material) for material in parsed_model.materials]


def build(parsed_model: ParsedModel, options: ModelBuildOptions) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    model_name = options.name or parsed_model.name

    if options.texture_folder_path is not None:
        material_builder.build_textures_from_file_system(parsed_model.materials, options.texture_folder_path, options.texture_allow_recurse, [options.texture_extension])

    armature_object = None
    if options.create_armature and parsed_model.skeleton is not None:
        armature_object = skeleton_builder.build(parsed_model.skeleton, model_name)

    parsed_meshes = parsed_model.meshes
    if options.merge_clusters:
        parsed_meshes = _merge_prepass(parsed_model)

    _build_materials(parsed_model)
    blender_materials = _build_materials(parsed_model)

    built_objects = []
    for parsed_mesh in parsed_meshes:
        obj = _build_mesh(parsed_model, parsed_mesh, armature_object, model_name=model_name, apply_lod_name_prefix=options.apply_lod_name_prefix, materials=blender_materials)
        built_objects.append(obj)

    if options.import_lights:
        light_parent = None
        if armature_object is not None:
            light_parent = armature_object
        elif len(built_objects) > 0:
            light_parent = built_objects[0]
        _build_lights(parsed_model, parent=light_parent)

    if options.hide_lods:
        _hide_lod_meshes(parsed_meshes, built_objects)

    return armature_object, built_objects