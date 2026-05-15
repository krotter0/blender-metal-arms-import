import bpy
import mathutils

from . import model_builder_dx, model_builder_gc
from ....common.platform import Platform
from ..types.model import Ape
from . import material_builder, skeleton_builder
from ....common import axis_convert
from ....formats.common.builders import light_builder

_PLATFORM_BUILDERS = {
    Platform.DX: model_builder_dx,
    Platform.GC: model_builder_gc
}

class ModelBuildOptions:
    def __init__(self):
        self.filepath: str = ""
        self.lod_index: int = None
        self.create_armature: bool = True
        self.merge_clusters: bool = False
        self.parent: bpy.types.Object = None
        self.name: str = None
        self.texture_folder_path: str = None
        self.texture_allow_recurse: bool = True

def _get_platform_builder(ape: Ape):
    if ape.platform not in _PLATFORM_BUILDERS:
        raise ValueError(f"Unsupported platform: {ape.platform}")
    return _PLATFORM_BUILDERS[ape.platform]

def build(ape: Ape, options: ModelBuildOptions = ModelBuildOptions()):
    precompute_data = precompute(ape)
    return build_from_precompute(precompute_data, options)
    
def build_from_precompute(precompute_data, options: ModelBuildOptions = ModelBuildOptions()):
    ape = precompute_data.ape
    platform_builder = _get_platform_builder(ape)

    armature_object = skeleton_builder.build(ape, options.name) if options.create_armature and len(ape.bones) > 0 else None
    if armature_object is not None and options.parent is not None:
        armature_object.parent = options.parent

    if options.texture_folder_path is not None:
        material_builder.build_textures_from_file_system(ape, options.texture_folder_path, options.texture_allow_recurse)
    
    mesh_objs = platform_builder.build_mesh_objs(precompute_data, armature_object, options.parent, options.lod_index)

    for i, light_init in enumerate(ape.lights):
        light = light_builder.build(i, light_init)
        if light_init.parent_bone_idx != -1 and armature_object is not None:
            bone = ape.bones[light_init.parent_bone_idx]
            
            bone_to_model_mtx = axis_convert.mtx43a_to_blender_mtx(bone.at_rest_bone_to_model_mtx)
            # Transform light location by bone rest matrix
            light_pos = bone_to_model_mtx @ mathutils.Vector(light.location)
            light.location = light_pos[:3]
            # Transform light rotation by bone rest matrix
            bone_rot_mtx = bone_to_model_mtx.to_3x3()
            light_rot_mtx = light.rotation_quaternion.to_matrix()
            light.rotation_quaternion = (bone_rot_mtx @ light_rot_mtx).to_quaternion()

            light.parent = armature_object
            light.parent_type = 'BONE'
            light.parent_bone = bone.name

    if options.merge_clusters and len(mesh_objs) > 0:
        bpy.context.view_layer.objects.active = mesh_objs[0]
        bpy.ops.object.select_all(action='DESELECT')
        for cluster in mesh_objs:
            cluster.select_set(True)
            
        dest_obj = armature_object if armature_object is not None else mesh_objs[0]
        merged_objs = [obj for obj in mesh_objs if obj != dest_obj]
        with bpy.context.temp_override(active_object=dest_obj, selected_objects=merged_objs):
            bpy.ops.object.join()
        dest_obj.name = options.name or ape.name
        return dest_obj
    
def precompute(ape: Ape):
    data = None
    platform_builder = _get_platform_builder(ape)
    data = platform_builder.ModelPrecomputeData(ape)
    data.precompute()
    return data