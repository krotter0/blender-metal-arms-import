import bpy
from ..parsers.models.skeleton import ParsedSkeleton
from ..parsers.skeleton_gc import SkeletonParserGC
from ..parsers.skeleton_dx import SkeletonParserDX
from ....common.platform import Platform
from mathutils import Vector, Matrix

from ..parsers.skeleton import ParsedBone, SkeletonParser
from ..types.model import FMesh_t

_MIN_BONE_LENGTH = 0.4

def _get_max_distance_to_children(bone: ParsedBone):
    bone_pos = Vector(bone.bone_to_model_matrix[3])
    max_distance = 0.0

    for child in bone.children:
        child_pos = Vector(child.bone_to_model_matrix[3])
        distance = (child_pos - bone_pos).length
        distance = max(distance, max_distance)

    return max_distance

def _build_bone(armature, bone: ParsedBone, parent_bone_obj: bpy.types.EditBone = None):
    bone_obj = armature.edit_bones.new(bone.name)

    distance_to_children = _get_max_distance_to_children(bone)
    bone_length = max(_MIN_BONE_LENGTH, distance_to_children)

    mtx = Matrix(bone.bone_to_model_matrix)
    y_dir = mtx.col[1].to_3d()
    z_dir = mtx.col[2].to_3d()

    head = mtx.to_translation()
    tail = head + y_dir * bone_length
    roll = z_dir
    
    bone_obj.use_relative_parent = True
    bone_obj.head = head
    bone_obj.tail = tail
    bone_obj.align_roll(roll)
    if parent_bone_obj is not None:
        bone_obj.parent = parent_bone_obj
    return bone_obj

def _build_bones(armature: bpy.types.Armature, root_bone: ParsedBone, parent_bone_obj: bpy.types.EditBone = None):
    bone_obj = _build_bone(armature, root_bone, parent_bone_obj)

    for child in root_bone.children:
        _build_bones(armature, child, bone_obj)

def build(parsed_skeleton: ParsedSkeleton, name: str):
    armature = bpy.data.armatures.new(name=name)

    armature_object = bpy.data.objects.new(name=name, object_data=armature)

    scene = bpy.context.scene
    scene.collection.objects.link(armature_object)

    bpy.context.view_layer.objects.active = armature_object
    
    bpy.ops.object.mode_set(mode='EDIT')

    for root_bone in parsed_skeleton.root_bones:
        _build_bones(armature, root_bone)

    bpy.ops.object.mode_set(mode='OBJECT')

    return armature_object