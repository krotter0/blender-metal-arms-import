from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ....structs.genericfieldtypes import *
from typing import Self
from enum import Enum

class EnumType(DynamicFormattedFieldType):
    def __init__(self, enum_type: type[Enum], size: int):
        self.enum_cls = enum_type
        format = None
        if size == 1: format = "B"
        elif size == 2: format = "H"
        elif size == 4: format = "I"
        elif size == 8: format = "Q"
        else: raise ValueError(f"Invalid size {size} for EnumType")
        super().__init__(size=size)
        self.struct = EndiannessStruct(format)
        
    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        value = super().read(memory, offset, raw)
        return self.enum_cls(value[0])
    
    def write(self, memory: VirtualMemory, offset: int, value: Enum, raw: bool = False):
        if not isinstance(value, self.enum_cls):
            raise ValueError(f"Expected value of type {self.enum_cls}, got {type(value)}")
        return super().write(memory, offset, (value.value,), raw)

class CFVec3(Struct):
    x: float = Field(f32)
    y: float = Field(f32)
    z: float = Field(f32)

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFVec3A(Struct):
    x: float = Field(f32)
    y: float = Field(f32)
    z: float = Field(f32)
    a: float = Field(f32)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFVec2(Struct):
    x: float = Field(f32)
    y: float = Field(f32)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFColorRGB(Struct):
    r: float = Field(f32)
    g: float = Field(f32)
    b: float = Field(f32)
    
    def __getitem__(self, key):
        if key == 0:
            return self.r
        elif key == 1:
            return self.g
        elif key == 2:
            return self.b
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFColorRGBA(Struct):
    r: float = Field(f32)
    g: float = Field(f32)
    b: float = Field(f32)
    a: float = Field(f32)

    def __getitem__(self, key):
        if key == 0:
            return self.r
        elif key == 1:
            return self.g
        elif key == 2:
            return self.b
        elif key == 3:
            return self.a
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")
        
class CFColorPackedRGB(Struct):
    r: int = Field(u8)
    g: int = Field(u8)
    b: int = Field(u8)

class CFColorPackedRGBA(Struct):
    r: int = Field(u8)
    g: int = Field(u8)
    b: int = Field(u8)
    a: int = Field(u8)

class CFSphere(Struct):
    radius: float = Field(f32)
    pos: CFVec3 = Field(CFVec3)

class CFQuatA(Struct):
    x: float = Field(f32)
    y: float = Field(f32)
    z: float = Field(f32)
    a: float = Field(f32)

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFMtx43A(Struct):
    x: CFVec3A = Field(CFVec3A)
    y: CFVec3A = Field(CFVec3A)
    z: CFVec3A = Field(CFVec3A)
    a: CFVec3A = Field(CFVec3A)

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFMtx43(Struct):
    x: CFVec3 = Field(CFVec3)
    y: CFVec3 = Field(CFVec3)
    z: CFVec3 = Field(CFVec3)
    a: CFVec3 = Field(CFVec3)

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError(f"Invalid index {key} for {self.__class__.__name__}")

class CFColorMotif(CFColorRGBA):
    motif_index: int = Field(u32)

class FLink_t(Struct):
    prev_link: Pointer[Self] = PointerTo(Self)
    next_link: Pointer[Self] = PointerTo(Self)

class FLinkRoot_t(Struct):
    head_link: Pointer[FLink_t] = PointerTo(FLink_t)
    tail_link: Pointer[FLink_t] = PointerTo(FLink_t)
    struct_offset: int = Field(s32)
    count: int = Field(u32)