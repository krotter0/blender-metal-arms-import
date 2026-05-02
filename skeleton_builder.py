from .axis_convert import to_blender_pos

from .reader.ape import Ape, FMeshBone_t

from . import vec
import bpy
import mathutils

MIN_BONE_LENGTH = 0.4

def get_max_distance_to_children(ape: Ape, bone_index: int, bone_children: list[FMeshBone_t]):
    bone = ape.boneArray[bone_index]
    bone_pos = bone.AtRestBoneToModelMtx.a
    max_distance = 0.0

    for child_index in bone_children[bone_index]:
        child_bone = ape.boneArray[child_index]
        child_pos = child_bone.AtRestBoneToModelMtx.a
        distance = vec.len(vec.sub(child_pos, bone_pos))
        if distance > max_distance:
            max_distance = distance

    return max_distance

def build_bone(ape: Ape, bone_index: int, bone_children: list[FMeshBone_t], armature):
    bone = ape.boneArray[bone_index]
    bone_obj = armature.edit_bones.new(bone.name)

    distance_to_children = get_max_distance_to_children(ape, bone_index, bone_children)
    bone_length = max(MIN_BONE_LENGTH, distance_to_children * 1)

    pos = bone.AtRestBoneToModelMtx.a
    head = to_blender_pos(pos)
    tail = vec.add(head, vec.mul((bone.AtRestBoneToModelMtx.z.x, bone.AtRestBoneToModelMtx.z.z, bone.AtRestBoneToModelMtx.z.y), bone_length))
    roll = mathutils.Vector((bone.AtRestBoneToModelMtx.y.x, bone.AtRestBoneToModelMtx.y.z, bone.AtRestBoneToModelMtx.y.y))

    bone_obj.use_relative_parent = True
    bone_obj.head = head
    bone_obj.tail = tail
    bone_obj.align_roll(roll)
    return bone_obj

def update_bone_hierarchy(ape: Ape, bone_index: int, bone_objs):
    bone = ape.boneArray[bone_index]
    if bone.Skeleton.parentBoneIndex == 255:
        return
    bone_objs[bone_index].parent = bone_objs[bone.Skeleton.parentBoneIndex]

def build_skeleton(ape: Ape):
    armature = bpy.data.armatures.new(name=ape.name)

    armature_object = bpy.data.objects.new(name=ape.name, object_data=armature)

    scene = bpy.context.scene
    scene.collection.objects.link(armature_object)

    bpy.context.view_layer.objects.active = armature_object
    
    bpy.ops.object.mode_set(mode='EDIT')

    bone_children = [[] for _ in ape.boneArray]
    for i, bone in enumerate(ape.boneArray):
        parent_index = bone.Skeleton.parentBoneIndex
        if parent_index != 255:
            bone_children[parent_index].append(i)

    bone_objs = [None] * len(ape.boneArray)
    for i, bone in enumerate(ape.boneArray):
        bone_objs[i] = build_bone(ape, i, bone_children, armature)
        
    for i, bone in enumerate(ape.boneArray):
        update_bone_hierarchy(ape, i, bone_objs)

    bpy.ops.object.mode_set(mode='OBJECT')

    return armature_object