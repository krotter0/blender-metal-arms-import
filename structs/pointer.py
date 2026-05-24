from typing import Generic, Iterator, Self, TypeVar
from .fieldtype import *

T = TypeVar("T", bound=FieldType)
class Pointer(Generic[T]):
    deref: T

    def __init__(self, memory: VirtualMemory, address: int, pointee_type: T | type[T]):
        if isinstance(pointee_type, type):
            pointee_type = pointee_type.get_instance()
            
        self.memory = memory
        self.address = address
        self.pointee_type = pointee_type
        self._pointee_size = None if pointee_type is None else pointee_type.get_size()

    def cast(self, new_pointee_type: T | type[T]):
        if isinstance(new_pointee_type, type):
            new_pointee_type = new_pointee_type()
        return Pointer(self.memory, self.address, new_pointee_type)
    
    def iterable(self, length: int | Self):
        if isinstance(length, int):
            return IterablePointer(self.memory, self.address, self.pointee_type, length)
        elif length is self:
            return IterablePointer(self.memory, self.address, self.pointee_type, length.address, length.pointee_type)
        else:
            raise ValueError(f"Invalid length parameter for iterable pointer: {length}")
        
    def cast_iterable(self, new_pointee_type: T | type[T], length: int | Self):
        return self.cast(new_pointee_type).iterable(length)

    def _get_deref(self):
        return self.pointee_type.read(self.memory, self.address)

    def _set_deref(self, value):
        return self.pointee_type.write(self.memory, self.address, value)
    
    def __getitem__(self, key) -> T:
        return self.pointee_type.read(self.memory, self.address + key * self._pointee_size)
    
    def __setitem__(self, key, value) -> T:
        return self.pointee_type.write(self.memory, self.address + key * self._pointee_size, value)

    def flatten(self):
        if self.address == 0:
            return None
        elif self.pointee_type is None:
            return self.address
        return self.pointee_type.flatten_type(self.memory, self.address)
    
    def __add__(self, other):
        offset = self.address
        if self._pointee_size is None:
            offset += other
        else:
            offset += other * self._pointee_size
        return Pointer(self.memory, offset, self.pointee_type)

    def __sub__(self, other):
        offset = self.address
        if self._pointee_size is None:
            offset -= other
        else:
            offset -= other * self._pointee_size
        return Pointer(self.memory, offset, self.pointee_type)
    

    def _get_deref_base(self):
        #if self.address == 0:
        #    raise ValueError("Cannot dereference null pointer")
        return self._get_deref()
    
    def _set_deref_base(self, value):
        #if self.address == 0:
        #    raise ValueError("Cannot dereference null pointer")
        return self._set_deref(value)
    
    deref = property(_get_deref_base, _set_deref_base)
    
    def __iter__(self):
        raise NotImplementedError(f"Pointer type '{self.__class__.__name__}' does not support iteration")
    
    def __len__(self):
        raise NotImplementedError(f"Pointer type '{self.__class__.__name__}' does not support length retrieval")



class IterablePointer(Pointer[T]):
    def __init__(self, memory: VirtualMemory, address: int, pointee_type: T | type[T], length_or_count_address: int, count_type: T | type[T] = None):
        super().__init__(memory, address, pointee_type)
        if isinstance(count_type, type):
            count_type = count_type.get_instance()
        self.length_or_count_address: int = length_or_count_address
        self.count_type: T | None = count_type

    def cast(self, new_pointee_type: T | type[T]):
        return IterablePointer(self.memory, self.address, new_pointee_type, self.length_or_count_address, self.count_type)

    def __iter__(self) -> Iterator[T]:
        count = self.__len__()
        if count <= 0:
            return
        
        for i in range(count):
            yield self[i]

    def __len__(self):
        if self.count_type is None:
            return self.length_or_count_address
        return self.count_type.read(self.memory, self.length_or_count_address)

    def flatten(self):
        count = self.__len__()
        elements = []
        for i in range(count):
            element_offset = self.address + i * self._pointee_size
            element_value = self.pointee_type.flatten_type(self.memory, element_offset)
            elements.append(element_value)
        return elements

class ArrayPointer(Pointer[T]):
    def __init__(self, memory: VirtualMemory, address: int, element_type: T, sizes: tuple[int]):
        super().__init__(memory, address, element_type)
        self.sizes = sizes
        size_len = len(sizes)
        if size_len == 1:
            self._getitem_mode = self._getitem_1d
            self._setitem_mode = self._setitem_1d
        elif size_len > 1:
            self._getitem_mode = self._getitem_nd
            self._setitem_mode = self._setitem_nd
        else:
            raise ValueError(f"Invalid array sizes {sizes}, must be non-empty tuple of positive integers")
    
    def _get_array_offset(self, key: tuple[int]):
        offset = key
        for i in range(1, len(self.sizes)):
            offset *= self.sizes[i]
        return offset * self.pointee_type.get_size()
    
    def __getitem__(self, key):
        return self._getitem_mode(key)
    
    def __setitem__(self, key, value):
        return self._setitem_mode(key, value)
    
    def _getitem_1d(self, key):
        return self.pointee_type.read(self.memory, self.address + key * self._pointee_size)
    
    def _setitem_1d(self, key, value):
        return self.pointee_type.write(self.memory, self.address + key * self._pointee_size, value)

    def _getitem_nd(self, key):
        offset = self._get_array_offset(key)
        return ArrayPointer(self.memory, self.address + offset, self.pointee_type, self.sizes[1:])
        
    def _setitem_nd(self, key, value):
        raise NotImplementedError("Setting non-leaf array elements is not supported")
    
    def __len__(self):
        return self.sizes[0]

    def __iter__(self):
        for i in range(self.sizes[0]):
            yield self[i]

class PointerFieldType(PrimitiveFieldType):
    STATIC = False
    FORMAT = "I"
    def __init__(self, pointee_type: FieldType):
        super().__init__()
        self.pointee_type = pointee_type

    def read(self, memory: VirtualMemory, offset: int, raw: bool = False):
        ptr_value = super().read(memory, offset, raw)
        if raw:
            return ptr_value
        
        return Pointer(memory, ptr_value, self.pointee_type)
    
    def write(self, memory: VirtualMemory, offset: int, value: any, raw: bool = False):
        ptr_value = value
        if not raw:
            ptr_value = value.address
        return super().write(memory, offset, (ptr_value,), raw)

    def flatten_type(self, memory: VirtualMemory, offset: int):
        pointer = self.read(memory, offset)
        return pointer.flatten()