from enum import Flag
from ....structs.structs import *
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.genericfieldtypes import *
from ...common.types.common import *

class AnimFlags(Flag):
    NONE = 0x0000
    COMP_TRANSLATION = 0x0001
    COMP_ORIENTATION = 0x0002
    BIT_8_SECS = 0x0010
    BIT_16_SECS = 0x0020
    BIT_8_FRAMECOUNT = 0x0040

class FAnimBone_t(Struct):
    name: Pointer[str] = PointerTo(NullTermString())
    scale_key_count: int = Field(u16)
    translation_key_count: int = Field(u16)
    orientation_key_count: int = Field(u16)
    Padding(2)
    scale_key_unit_time_ptr: Pointer[None] = VoidPointer()
    translation_key_unit_time_ptr: Pointer[None] = VoidPointer()
    orientation_key_unit_time_ptr: Pointer[None] = VoidPointer()
    scale_key_data_ptr: Pointer[None] = VoidPointer()
    translation_key_data_ptr: Pointer[None] = VoidPointer()
    orientation_key_data_ptr: Pointer[None] = VoidPointer()

class FAnim_t(Struct):
    name: str = Field(FixedSizeString(16))
    flags: AnimFlags = Field(EnumType(AnimFlags, 2))
    bone_count: int = Field(u16)
    total_seconds: float = Field(f32)
    oo_total_seconds: float = Field(f32)
    bone_array: IterablePointer[FAnimBone_t] = PointerToIterable(FAnimBone_t, 'bone_count')