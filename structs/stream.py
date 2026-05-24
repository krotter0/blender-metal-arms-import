from .pointer import Pointer
from .fieldtype import *
from .virtualmemory import *

class Stream():
    def __init__(self, memory: VirtualMemory, offset: int = 0):
        self.memory = memory
        self.offset = offset

    def read(self, field_type: FieldType | type[FieldType], raw: bool = False):
        if isinstance(field_type, type):
            field_type = field_type.get_instance()

        offset = self.offset
        self.offset += field_type.get_size()
        return field_type.read(self.memory, offset, raw=raw)

    def write(self, field_type: FieldType | type[FieldType], value: any, raw: bool = False):
        if isinstance(field_type, type):
            field_type = field_type.get_instance()
        
        field_type.write(self.memory, self.offset, value, raw=raw)
        self.offset += field_type.get_size() 

    @staticmethod
    def from_pointer(pointer: Pointer):
        stream = Stream(pointer.memory, pointer.address)
        return stream