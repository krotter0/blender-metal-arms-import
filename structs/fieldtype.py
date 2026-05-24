from typing import Self
from .virtualmemory import *

class FieldTypeMeta(type):
    def __new__(cls, clsname, bases, attrs: dict):
        newcls = super().__new__(cls, clsname, bases, attrs)
        instance = None

        any_base_static = any(getattr(base, "STATIC", False) for base in bases)
        
        if attrs.get("STATIC", any_base_static):
            instance = newcls()
            attrs["STATIC"] = True
            
        setattr(newcls, "INSTANCE", instance)
        return newcls

class FormattedFieldTypeMeta(FieldTypeMeta):
    def __new__(cls, clsname, bases, attrs: dict):
        if "FORMAT" in attrs:
            format = attrs["FORMAT"]
            struct = EndiannessStruct(format)
            attrs["STRUCT"] = struct
            try:
                format_size = struct.size
                attrs["SIZE"] = format_size
            except struct.error as e:
                raise ValueError(f"Invalid FORMAT string for field type {clsname}: {e}")
        else:
            attrs["STRUCT"] = None
            attrs["SIZE"] = None
            
        return super().__new__(cls, clsname, bases, attrs)

class FieldType(metaclass=FieldTypeMeta):
    INSTANCE: Self
    STATIC = True

    def __init__(self, size=None):
        self._size = size

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        raise NotImplementedError(f"Read method not implemented for field type {self.__class__.__name__}")
    
    def write(self, memory: VirtualMemory, offset: int, value: any, raw: bool = False):
        raise NotImplementedError(f"Write method not implemented for field type {self.__class__.__name__}")

    def flatten_type(self, memory: VirtualMemory, offset: int):
        return self.read(memory, offset)
    
    def get_size(self):
        if self._size is None:
            return self.SIZE
        return self._size
    
    def set_size(self, value):
        self._size = value

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE is None:
            return cls()
        return cls.INSTANCE

class FormattedFieldType(FieldType, metaclass=FormattedFieldTypeMeta):
    def __init__(self, size=None):
        super().__init__(size=size)

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        return memory.read_struct(self.struct, offset)
    
    def write(self, memory: VirtualMemory, offset: int, value: tuple, raw: bool = False):
        return memory.write_struct(self.struct, value, offset)
    
    def _get_struct(self):
        return self.STRUCT
    
    def _set_struct(self, value):
        raise ValueError(f"Struct cannot be set for non-dynamic formatted field type {type(self).__name__}")

    def _struct_getter(self):
        return self._get_struct()
    
    def _struct_setter(self, value):
        return self._set_struct(value)

    struct = property(_struct_getter, _struct_setter)

class DynamicFormattedFieldType(FormattedFieldType):
    STATIC = False
    def __init__(self, size=None):
        super().__init__(size=size)
        self._struct: EndiannessStruct = self.STRUCT
    
    def _get_struct(self):
        return self._struct
    
    def _set_struct(self, value):
        self._struct = value
        self.set_size(value.size)

class ArrayFieldType(FieldType):
    STATIC = False

    def __init__(self, element_type: FieldType, sizes: list[int]):
        if isinstance(sizes, int):
            sizes = [sizes]
        if isinstance(element_type, type):
            element_type = element_type.get_instance()
        total_sizes = 0
        for s in sizes:
            if s <= 0:
                raise ValueError(f"Invalid array size {s}, must be positive integer")
            total_sizes += s

        type_size = element_type.get_size() * total_sizes
        super().__init__(size=type_size)
        self.element_type = element_type
        self.array_sizes = sizes

    def flatten_type(self, memory: VirtualMemory, offset: int):
        elements = []
        for i in range(self.array_sizes[0]):
            element_offset = offset + i * self.element_type.get_size()
            element_value = self.element_type.flatten_type(memory, element_offset)
            elements.append(element_value)
        return elements

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        elements = []
        for i in range(self.array_sizes[0]):
            element_offset = offset + i * self.element_type.get_size()
            element_value = self.element_type.read(memory, element_offset, raw=raw)
            elements.append(element_value)
        return elements

class PrimitiveFieldType(FormattedFieldType):
    def __init__(self):
        super().__init__()

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        return super().read(memory, offset, raw)[0]
    
    def write(self, memory: VirtualMemory, offset: int, value: any, raw: bool = False):
        return super().write(memory, offset, (value,), raw)
    
class NullTermString(FieldType):
    SIZE = None
    
    def __init__(self, wide: bool = False):
        super().__init__()
        self._char_size = 2 if wide else 1
        self._string_format = "utf-16" if wide else "ascii"

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        bytes_list = []
        while True:
            byte = memory.read(self._char_size, offset)
            if len(byte) == 0:
                raise ValueError(f"Reached end of memory while reading null-terminated string at offset {offset}")
            
            if byte == b"\x00" * self._char_size:
                break
            bytes_list.append(byte)
            offset += self._char_size
        return b"".join(bytes_list).decode(self._string_format)
    
    def write(self, memory: VirtualMemory, offset: int, value: str, raw: bool = False):
        encoded_bytes = value.encode(self._string_format) + b"\x00" * self._char_size
        memory.write(encoded_bytes, offset)

class FixedSizeString(DynamicFormattedFieldType):
    STATIC = False
    def __init__(self, length: int, wide: bool = False):
        char_size = 2 if wide else 1
        size = length * char_size
        super().__init__(size=size)
        self.format = f"{size}s"
        self.struct = EndiannessStruct(self.format)
        self._string_format = "utf-16" if wide else "ascii"

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        raw_bytes = super().read(memory, offset, raw)[0]
        null_terminated_bytes = raw_bytes.split(b"\x00", 1)[0]
        string = null_terminated_bytes.decode(self._string_format)
        return string
    
    def write(self, memory: VirtualMemory, offset: int, value: str, raw: bool = False):
        encoded_bytes = value.encode(self._string_format)
        size = self.get_size()
        if len(encoded_bytes) > size:
            raise ValueError(f"String is too long to fit in fixed size field (max {size} bytes, got {len(encoded_bytes)} bytes)")
        padded_bytes = encoded_bytes.ljust(size, b"\x00")
        super().write(memory, offset, (padded_bytes,), raw)