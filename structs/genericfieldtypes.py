from .fieldtype import *
from .virtualmemory import *

class BOOL(PrimitiveFieldType):
    FORMAT = "I"
    def read(self, memory: VirtualMemory, offset: int):
        return super().read(memory, offset) != 0
    
    def write(self, memory: VirtualMemory, offset: int, value: any):
        return super().write(memory, offset, (1 if value else 0,))
    
class BOOL8(BOOL): FORMAT = "B"
class f64(PrimitiveFieldType): FORMAT = "d"
class u64(PrimitiveFieldType): FORMAT = "Q"
class s64(PrimitiveFieldType): FORMAT = "q"
class f32(PrimitiveFieldType): FORMAT = "f"
class u32(PrimitiveFieldType): FORMAT = "I"
class s32(PrimitiveFieldType): FORMAT = "i"
class u16(PrimitiveFieldType): FORMAT = "H"
class s16(PrimitiveFieldType): FORMAT = "h"
class u8(PrimitiveFieldType): FORMAT = "B"
class s8(PrimitiveFieldType): FORMAT = "b"