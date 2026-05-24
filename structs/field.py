from .fieldtype import *
from .pointer import *

class BaseField:
    field_name: str

    def __init__(self, size: int, offset: int = 0):
        self.field_size = size
        self.field_offset = offset

    def set_name(self, name: str):
        self.field_name = name

    def set_offset(self, offset: int):
        self.field_offset = offset

    def read(self, memory: VirtualMemory, offset: int):
        raise NotImplementedError(f"Read method not implemented for field {self.__class__.__name__}")
    
    def write(self, memory: VirtualMemory, offset: int, value: any):
        raise NotImplementedError(f"Write method not implemented for field {self.__class__.__name__}")
    
    def init_field(self, fields: dict[str, Self]):
        pass

class TagModifier:
    def __init__(self, tag: any, field: BaseField):
        self.field = field
        self.tag = tag

    def is_active(self, tag_set: set):
        return NotImplementedError("is_active() method not implemented for TagModifier")

class RequiresTag(TagModifier):
    def is_active(self, tag_set: set):
        return self.tag in tag_set

class Field(BaseField):
    def __init__(self, field_type: FieldType | type[FieldType]):
        if isinstance(field_type, type):
            field_type = field_type()
        super().__init__(size=field_type.get_size())
        self.field_type = field_type

    def read(self, memory: VirtualMemory, offset: int):
        return self.field_type.read(memory, offset)
    
    def write(self, memory: VirtualMemory, offset: int, value: any):
        return self.field_type.write(memory, offset, value)

def _normalize_field_type(field_type: FieldType | type[FieldType] | Field) -> FieldType:
    if isinstance(field_type, type):
        return field_type()
    elif isinstance(field_type, Field):
        return field_type.field_type
    return field_type

class PointerField(Field):
    DYNAMIC = True
    POINTER_FIELD_TYPE = PointerFieldType
    field_type: PointerFieldType

    def __init__(self, pointee_type: FieldType | type[FieldType] | Field | None):
        pointee_type = _normalize_field_type(pointee_type) if pointee_type is not None else None
        super().__init__(field_type=self.POINTER_FIELD_TYPE(pointee_type))

    def _construct_pointer(self, memory: VirtualMemory, self_offset: int, pointer_value: int):
        return Pointer(memory, pointer_value, self.field_type.pointee_type)

    def read(self, memory: VirtualMemory, offset: int):
        pointer_value = self.field_type.read(memory, offset, raw=True)
        #if pointer_value == 0:
        #    return None
        return self._construct_pointer(memory, offset, pointer_value)
        
    def write(self, memory: VirtualMemory, offset: int, value: any):
        if value is None:
            pointer_value = 0
        elif isinstance(value, Pointer):
            pointer_value = value.address
        else:
            pointer_value = value
        return super().write(memory, offset, pointer_value)
    
    def cast(self, new_pointee_type: FieldType | type[FieldType] | Field | None):
        return self.__class__(new_pointee_type)
    
class IterablePointerField(PointerField):
    def __init__(self, pointee_type: FieldType | type[FieldType] | Field | None, count_field_name: str):
        super().__init__(pointee_type)
        self.count_field_name = count_field_name
        self._count_field_type: FieldType | None = None
        self._count_field_offset: int | None = None

    def init_field(self, fields: dict[str, Field]):
        super().init_field(fields)
        count_field = fields.get(self.count_field_name)
        if count_field is None:
            raise ValueError(f"Count field '{self.count_field_name}' not found for iterable pointer field")
        count_offset_to_self = count_field.field_offset - self.field_offset
        self._set_count_field(count_offset_to_self, count_field.field_type)

    def _set_count_field(self, offset: int, type: FieldType | type[FieldType] | Field):
        type = _normalize_field_type(type)
        self._count_field_type = type
        self._count_field_offset = offset

    def _construct_pointer(self, memory: VirtualMemory, self_offset: int, pointer_value: int):
        if self._count_field_type is None or self._count_field_offset is None:
            raise ValueError(f"Count field for iterable pointer field '{self.count_field_name}' is not set")
        return IterablePointer(memory, pointer_value, self.field_type.pointee_type, self_offset + self._count_field_offset, self._count_field_type)

    def cast(self, new_pointee_type: FieldType | type[FieldType] | Field | None):
        return self.__class__(new_pointee_type, self.count_field_name)

class VoidPointerField(PointerField):
    def __init__(self):
        super().__init__(pointee_type=None)
 
class ArrayField(Field):
    def __init__(self, element_type: FieldType | type[FieldType] | Field, sizes: int | tuple[int]):
        if isinstance(sizes, int):
            sizes = (sizes,)

        element_type = _normalize_field_type(element_type)
        super().__init__(field_type=ArrayFieldType(element_type, sizes))

    def read(self, memory: VirtualMemory, offset: int):
        return ArrayPointer(memory, offset, self.field_type.element_type, self.field_type.array_sizes)

ArrayOf = ArrayField #Alias
PointerTo = PointerField #Alias
PointerToIterable = IterablePointerField #Alias
VoidPointer = VoidPointerField #Alias