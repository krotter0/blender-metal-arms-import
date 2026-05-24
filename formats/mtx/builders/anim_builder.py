from ..parsers.models.animation import ParsedAnimation

import bpy
import mathutils
from bpy_extras import anim_utils
from ....structs.genericfieldtypes import *
from ....common.axis_convert import to_blender_rot, to_blender_pos
        
def _get_rest_local_components(armature_bone):
    rest_matrix = armature_bone.matrix_local.copy()
    if armature_bone.parent is not None:
        rest_matrix = armature_bone.parent.matrix_local.inverted() @ rest_matrix

    rest_location, rest_rotation, _ = rest_matrix.decompose()
    return rest_location, rest_rotation

def _insert_keyframes(channelbag, data_path, values_by_time, value_count):
    for index in range(value_count):
        fcurve = channelbag.fcurves.ensure(data_path, index=index)
        fcurve.extrapolation = 'CONSTANT'
        fcurve.keyframe_points.add(len(values_by_time))

        for key_index, (frame, value) in enumerate(values_by_time):
            keyframe = fcurve.keyframe_points[key_index]
            keyframe.co = (frame, value[index])
            keyframe.interpolation = 'LINEAR'

        fcurve.update()

def build(anim: ParsedAnimation, name, frame_rate=30, first_frame=1):
    obj = bpy.context.active_object

    if not obj.animation_data:
        obj.animation_data_create()

    animation_data = obj.animation_data
    action = bpy.data.actions.new(name=name)
    action.frame_range = (0, anim.total_seconds * frame_rate)
    action.frame_end = anim.total_seconds * frame_rate
    slot = action.slots.new(id_type=obj.id_type, name=obj.name)
    animation_data.action = action

    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)

    for bone_name, bone in anim.bones.items():
        if bone_name not in obj.data.bones or bone_name not in obj.pose.bones:
            continue

        translation_key_data = bone.translation_key_data
        orientation_key_data = bone.orientation_key_data
        scale_key_data = bone.scale_key_data

        translation_key_times = bone.translation_key_times
        orientation_key_times = bone.orientation_key_times
        scale_key_times = bone.scale_key_times

        obj.pose.bones[bone_name].rotation_mode = 'QUATERNION'
        rest_location, rest_rotation = _get_rest_local_components(obj.data.bones[bone_name])
        rest_rotation_inverse = rest_rotation.inverted()

        time_offset = first_frame

        if len(translation_key_data) > 0:
            location_keys = []
            for i in range(len(translation_key_data)):
                source_location = mathutils.Vector(to_blender_pos(translation_key_data[i]))
                pose_location = rest_rotation_inverse @ (source_location - rest_location)
                time = translation_key_times[i] * frame_rate + time_offset
                location_keys.append((time, tuple(pose_location)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone_name}"].location',
                location_keys,
                3,
            )

        if len(orientation_key_data) > 0:
            rotation_keys = []
            for i in range(len(orientation_key_data)):
                source_rotation = mathutils.Quaternion(to_blender_rot(orientation_key_data[i]))
                pose_rotation = rest_rotation_inverse @ source_rotation
                pose_rotation.normalize()
                time = orientation_key_times[i] * frame_rate + time_offset
                rotation_keys.append((time, tuple(pose_rotation)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone_name}"].rotation_quaternion',
                rotation_keys,
                4,
            )

        if len(scale_key_data) > 0:
            scale_keys = []
            for i in range(len(scale_key_data)):
                source_scale = scale_key_data[i]
                time = scale_key_times[i] * frame_rate + time_offset
                scale_keys.append((time, (source_scale, source_scale, source_scale)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone_name}"].scale',
                scale_keys,
                3,
            )