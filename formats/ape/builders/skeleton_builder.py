from ....common.axis_convert import to_blender_pos
from ..types.model import Ape
from ..types.skeleton import FMeshBone_t
from ....common import vec

import bpy
import mathutils

_MIN_BONE_LENGTH = 0.4

def _get_max_distance_to_children(ape: Ape, bone_index: int, bone_children: list[FMeshBone_t]):
    bone = ape.bones[bone_index]
    bone_pos = bone.at_rest_bone_to_model_mtx.a
    max_distance = 0.0

    for child_index in bone_children[bone_index]:
        child_bone = ape.bones[child_index]
        child_pos = child_bone.at_rest_bone_to_model_mtx.a
        distance = vec.len(vec.sub(child_pos, bone_pos))
        if distance > max_distance:
            max_distance = distance

    return max_distance

def _build_bone(ape: Ape, bone_index: int, bone_children: list[FMeshBone_t], armature):
    bone = ape.bones[bone_index]
    bone_obj = armature.edit_bones.new(bone.name)

    distance_to_children = _get_max_distance_to_children(ape, bone_index, bone_children)
    bone_length = max(_MIN_BONE_LENGTH, distance_to_children * 1)

    pos = bone.at_rest_bone_to_model_mtx.a
    head = to_blender_pos(pos)
    tail = vec.add(head, vec.mul((bone.at_rest_bone_to_model_mtx.z.x, bone.at_rest_bone_to_model_mtx.z.z, bone.at_rest_bone_to_model_mtx.z.y), bone_length))
    roll = mathutils.Vector((bone.at_rest_bone_to_model_mtx.y.x, bone.at_rest_bone_to_model_mtx.y.z, bone.at_rest_bone_to_model_mtx.y.y))

    bone_obj.use_relative_parent = True
    bone_obj.head = head
    bone_obj.tail = tail
    bone_obj.align_roll(roll)
    return bone_obj

def _update_bone_hierarchy(ape: Ape, bone_index: int, bone_objs):
    bone = ape.bones[bone_index]
    if bone.skeleton.parent_bone_index == 255:
        return
    bone_objs[bone_index].parent = bone_objs[bone.skeleton.parent_bone_index]

def build(ape: Ape, name: str = None):
    name = name or ape.name
    armature = bpy.data.armatures.new(name=name)

    armature_object = bpy.data.objects.new(name=name, object_data=armature)

    scene = bpy.context.scene
    scene.collection.objects.link(armature_object)

    bpy.context.view_layer.objects.active = armature_object
    
    bpy.ops.object.mode_set(mode='EDIT')

    bone_children = [[] for _ in ape.bones]
    for i, bone in enumerate(ape.bones):
        parent_index = bone.skeleton.parent_bone_index
        if parent_index != 255:
            bone_children[parent_index].append(i)

    bone_objs = [None] * len(ape.bones)
    for i, bone in enumerate(ape.bones):
        bone_objs[i] = _build_bone(ape, i, bone_children, armature)
        
    for i, bone in enumerate(ape.bones):
        _update_bone_hierarchy(ape, i, bone_objs)

    bpy.ops.object.mode_set(mode='OBJECT')

    return armature_object