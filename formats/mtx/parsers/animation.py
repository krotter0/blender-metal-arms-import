from ..types.anim import AnimFlags, FAnim_t, FAnimBone_t
from ...common.types.common import CFVec3, CFQuatA
from ....structs.genericfieldtypes import *
from ....structs.pointer import Pointer
from .models.animation import ParsedAnimation, ParsedAnimationBone

class AnimParser:
    _TRANSLATION_FRAC_BITS      = 8
    _COMP_TRANSLATION_CONVERTER = (1.0 / (1 << _TRANSLATION_FRAC_BITS))
    _ORIENTATION_FRAC_BITS      = 14
    _COMP_ORIENTATION_CONVERTER = (1.0 / (1 << _ORIENTATION_FRAC_BITS))

    def _read_times(self, ptr: Pointer[None], count: int, total_seconds: float, flags: AnimFlags):
        times = []
        ptr_type = f32
        divisor = 1.0
        if flags & AnimFlags.BIT_16_SECS:
            ptr_type = u16
            divisor = 32768.0
        elif flags & AnimFlags.BIT_8_SECS:
            ptr_type = u8
            divisor = 128.0

        ptr = ptr.cast(ptr_type).iterable(count)
        for time in ptr:
            times.append(time / divisor * total_seconds)
        return times

    def _read_scalings(self, ptr: Pointer[None], count: int):
        scale_key_data = []
        ptr = ptr.cast(f32).iterable(count)
        for scale in ptr:
            scale_key_data.append(scale)
        return scale_key_data

    def _read_orientations(self, ptr: Pointer[None], count: int, flags: AnimFlags):
        if flags & AnimFlags.COMP_ORIENTATION:
            return self._read_compressed_orientations(ptr, count)
        else:
            return self._read_uncompressed_orientations(ptr, count)

    def _read_translations(self, ptr: Pointer[None], count: int, flags: AnimFlags):
        if flags & AnimFlags.COMP_TRANSLATION:
            return self._read_compressed_translations(ptr, count)
        else:
            return self._read_uncompressed_translations(ptr, count)

    def _read_compressed_orientations(self, ptr: Pointer[None], count: int):
        orientation_key_data = []
        ptr = ptr.cast(ArrayFieldType(s16, 4)).iterable(count)
        for data in ptr:
            data = (data[0] * self._COMP_ORIENTATION_CONVERTER,
                    data[1] * self._COMP_ORIENTATION_CONVERTER,
                    data[2] * self._COMP_ORIENTATION_CONVERTER,
                    data[3] * self._COMP_ORIENTATION_CONVERTER)
            orientation_key_data.append(data)
        return orientation_key_data

    def _read_uncompressed_orientations(self, ptr: Pointer[None], count: int):
        orientation_key_data = []
        ptr = ptr.cast(CFQuatA).iterable(count)
        for data in ptr:
            orientation_key_data.append(data)
        return orientation_key_data

    def _read_compressed_translations(self, ptr: Pointer[None], count: int):
        translation_key_data = []
        ptr = ptr.cast(ArrayFieldType(s16, 3)).iterable(count)
        for data in ptr:
            data = (data[0] * self._COMP_TRANSLATION_CONVERTER,
                    data[1] * self._COMP_TRANSLATION_CONVERTER,
                    data[2] * self._COMP_TRANSLATION_CONVERTER)
            translation_key_data.append(data)
        return translation_key_data

    def _read_uncompressed_translations(self, ptr: Pointer[None], count: int):
        translation_key_data = []
        ptr = ptr.cast(CFVec3).iterable(count)
        for data in ptr:
            data = (data[0], data[1], data[2])
            translation_key_data.append(data)
        return translation_key_data
    
    def _parse_bone(self, bone: FAnimBone_t, total_seconds: float, flags: AnimFlags):
        translation_key_data = self._read_translations(bone.translation_key_data_ptr, bone.translation_key_count, flags)
        orientation_key_data = self._read_orientations(bone.orientation_key_data_ptr, bone.orientation_key_count, flags)
        scale_key_data = self._read_scalings(bone.scale_key_data_ptr, bone.scale_key_count)

        translation_key_times = self._read_times(bone.translation_key_unit_time_ptr, bone.translation_key_count, total_seconds, flags)
        orientation_key_times = self._read_times(bone.orientation_key_unit_time_ptr, bone.orientation_key_count, total_seconds, flags)
        scale_key_times = self._read_times(bone.scale_key_unit_time_ptr, bone.scale_key_count, total_seconds, flags)

        return ParsedAnimationBone(
            translation_key_data=translation_key_data,
            orientation_key_data=orientation_key_data,
            scale_key_data=scale_key_data,
            translation_key_times=translation_key_times,
            orientation_key_times=orientation_key_times,
            scale_key_times=scale_key_times,
        )

    def parse(self, anim: FAnim_t):
        total_seconds = anim.total_seconds
        flags = anim.flags
        parsed_bones = {bone.name.deref: self._parse_bone(bone, total_seconds, flags) for bone in anim.bone_array}
        return ParsedAnimation(
            flags=flags,
            total_seconds=total_seconds,
            bones=parsed_bones,
        )
