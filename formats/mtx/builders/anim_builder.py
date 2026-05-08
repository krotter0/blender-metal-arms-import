import bpy
import mathutils
from bpy_extras import anim_utils
from ..reader import Mtx
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

def create_action(mtx: Mtx, name, frame_rate=30):
    obj = bpy.context.active_object

    if not obj.animation_data:
        obj.animation_data_create()

    animation_data = obj.animation_data
    action = bpy.data.actions.new(name=name)
    action.frame_range = (0, mtx.totalSeconds * frame_rate)
    action.frame_end = mtx.totalSeconds * frame_rate
    slot = action.slots.new(id_type=obj.id_type, name=obj.name)
    animation_data.action = action

    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)

    for bone in mtx.boneArray:
        if bone.name not in obj.data.bones or bone.name not in obj.pose.bones:
            continue

        obj.pose.bones[bone.name].rotation_mode = 'QUATERNION'
        rest_location, rest_rotation = _get_rest_local_components(obj.data.bones[bone.name])
        rest_rotation_inverse = rest_rotation.inverted()

        if bone.tKeyCount:
            location_keys = []
            for i in range(bone.tKeyCount):
                source_location = mathutils.Vector(to_blender_pos(bone.tKeyData[i]))
                pose_location = rest_rotation_inverse @ (source_location - rest_location)
                location_keys.append((bone.tKeyTimes[i] * frame_rate, tuple(pose_location)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone.name}"].location',
                location_keys,
                3,
            )

        if bone.oKeyCount:
            rotation_keys = []
            for i in range(bone.oKeyCount):
                source_rotation = mathutils.Quaternion(to_blender_rot(bone.oKeyData[i]))
                pose_rotation = rest_rotation_inverse @ source_rotation
                pose_rotation.normalize()
                rotation_keys.append((bone.oKeyTimes[i] * frame_rate, tuple(pose_rotation)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone.name}"].rotation_quaternion',
                rotation_keys,
                4,
            )

        if bone.sKeyCount:
            scale_keys = []
            for i in range(bone.sKeyCount):
                source_scale = bone.sKeyData[i]
                scale_keys.append((bone.sKeyTimes[i] * frame_rate, (source_scale, source_scale, source_scale)))

            _insert_keyframes(
                channelbag,
                f'pose.bones["{bone.name}"].scale',
                scale_keys,
                3,
            )