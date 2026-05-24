from io import BytesIO, IOBase
from typing import Self
from pathlib import Path

from .virtualmemory import *
from .field import *
from .fieldtype import *

class Padding:
    def __init__(self, size: int):
        self.size = size

Skip = Padding #Alias

class BeginUnion():
    pass

class EndUnion():
    pass

class StructNamespace(dict):
    def __init__(self):
        super().__init__()
        self._pad_count = 0
        self._union_count = 0
        self._in_union = False
        self["Padding"] = self._set_padding
        self["BeginUnion"] = self._begin_union
        self["EndUnion"] = self._end_union

    def _set_padding(self, size: int):
        self[f"_pad{self._pad_count}"] = Padding(size)
        self._pad_count += 1

    def _begin_union(self):
        if self._in_union:
            raise ValueError("Cannot begin a new union while already in a union")
        self[f"_union_begin{self._union_count}"] = BeginUnion()
        self._in_union = True

    def _end_union(self):
        if not self._in_union:
            raise ValueError("Cannot end a union while not in a union")
        self[f"_union_end{self._union_count}"] = EndUnion()
        self._union_count += 1
        self._in_union = False

class StructMeta(FieldTypeMeta):
    baseclass: type['Struct'] = None

    @classmethod
    def __prepare__(cls, name, bases):
        return StructNamespace()
    
    def __new__(cls, clsname, bases, attrs):
        if FlatStruct in bases:
            return super().__new__(cls, clsname, bases, attrs)

        fields = {}
        offset = 0
        modifiers: list[TagModifier] = []

        fields_dependant_on_modifiers: dict[str, TagModifier] = {}
        inherited_types = 0
        for base in bases:
            if cls.baseclass is not None and issubclass(base, cls.baseclass):
                inherited_types += 1
                if inherited_types > 1:
                    raise NotImplementedError(f"Struct '{clsname}' cannot inherit from more than one struct class (inherited from '{base.__name__}')")
            if hasattr(base, "FIELDS"):
                fields.update(base.FIELDS)
            if hasattr(base, "SIZE"):
                offset += base.SIZE
            if hasattr(base, "TAG_MODIFIERS"):
                modifiers.extend(base.TAG_MODIFIERS)
            if hasattr(base, "_FIELDS_DEPENDANT_ON_FIELD_MODIFIERS"):
                fields_dependant_on_modifiers.update(base._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS)

        in_union = False
        union_size = 0
        for key, value in attrs.items():
            if isinstance(value, BeginUnion):
                if in_union:
                    raise ValueError(f"Cannot begin a new union while already in a union")
                in_union = True
            elif isinstance(value, EndUnion):
                if not in_union:
                    raise ValueError(f"Cannot end a union while not in a union")
                if union_size == 0:
                    raise ValueError(f"Union must contain at least one field")
                in_union = False
                offset += union_size
                union_size = 0
            elif isinstance(value, Padding):
                if in_union:
                    union_size = max(union_size, value.size)
                else:
                    offset += value.size
            elif isinstance(value, BaseField):
                field = value
                if isinstance(field, Field) and isinstance(field.field_type, Struct) and len(field.field_type.TAG_MODIFIERS) > 0:
                    raise NotImplementedError(f"Struct fields containing tag modifiers are not supported (field '{key}' in struct '{clsname}')")
                    
                cls._process_field(key, field, offset, clsname)
                fields[key] = field
                if in_union:
                    union_size = max(union_size, field.field_size)
                else:
                    offset += field.field_size
            elif isinstance(value, FieldType):
                raise ValueError(f"Field '{key}' in struct '{clsname}' is missing a Field wrapper")
            elif isinstance(value, TagModifier):
                if not in_union:
                    raise NotImplementedError(f"Tag modifiers are required to be inside unions (field '{key}' in struct '{clsname}')")
                
                field = value.field
                
                cls._process_field(key, field, offset, clsname)
                fields[key] = field

                modifiers.append(value)
                fields_dependant_on_modifiers[key] = value
                union_size = max(union_size, field.field_size)
        attrs["FIELDS"] = fields
        attrs["SIZE"] = offset
        attrs["TAG_MODIFIERS"] = modifiers
        attrs["_FIELDS_DEPENDANT_ON_FIELD_MODIFIERS"] = fields_dependant_on_modifiers

        if "EXPECTED_SIZE" in attrs:
            expected_size = attrs["EXPECTED_SIZE"]
            if offset != expected_size:
                raise ValueError(f"Struct '{clsname}' has size {offset} but expected size is {expected_size}")

        newcls: Struct = super().__new__(cls, clsname, bases, attrs)
        if cls.baseclass is None:
            cls.baseclass = newcls

        for key, field in fields.items():
            if isinstance(field, PointerField) and field.field_type.pointee_type == Self:
                field = field.cast(newcls)
                fields[key] = field

            field.init_field(fields)

            property = newcls._get_property_for_field(key, field)
            setattr(newcls, key, property)
            
        cls._build_flat_type(newcls, fields)

        return newcls
    
    def _process_field(key: str, field: BaseField, offset: int, clsname: str):
        field.set_offset(offset)
        size = field.field_size
        if size is None:
            raise ValueError(f"Field '{key}' in struct '{clsname}' has an undefined size")
        
        field.set_name(key)
    
    def _build_flat_type(cls, fields):
        name = f"{cls.__name__}Flat"
        flat_type = type(name, (FlatStruct, cls), {})
        for key, field in fields.items():
            def getter(self, key=key):
                return self._get_field_value(key)
            
            def setter(self, value, key=key):
                return self._set_field_value(value, key)
            
            setattr(flat_type, key, property(getter, setter))
        setattr(cls, "FLAT_TYPE", flat_type)

class FlatStruct(dict):
    def _get_field_value(self, key):
        return self[key]
    
    def _set_field_value(self, value, key):
        self[key] = value

class Struct(FieldType, metaclass=StructMeta):
    STATIC = False
    FIELDS: dict[str, Field]
    FLAT_TYPE: type[FlatStruct|Self]
    TAG_MODIFIERS: list[TagModifier]
    _FIELDS_DEPENDANT_ON_FIELD_MODIFIERS: dict[str, TagModifier]
    
    def __init__(self):
        super().__init__()
        self._memory: VirtualMemory | None = None
        self._address: int = 0
        self._flat = False

    def _get_memory(self):
        if self._memory is None:
            raise ValueError("Struct is not bound to memory")
        return self._memory

    memory: VirtualMemory = property(_get_memory)

    def _calculate_size(self):
        size = self.SIZE
        tags = self._memory._get_tags()
        for field_key, modifier in self._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS.items():
            if modifier.is_active(tags):
                field = self.FIELDS[field_key]
                size += field.field_size
        return size

    def bind(self, memory: VirtualMemory, offset: int = 0):
        if self._flat:
            raise ValueError("Cannot bind a flattened struct to memory")
        self._memory = memory
        self._address = offset
        return self

    def bind_to_io(self, io: IOBase, offset: int = 0, big_endian: bool = None, tags: Iterable[any] = ()):
        if self._flat:
            raise ValueError("Cannot bind a flattened struct to memory")
        memory = VirtualMemory(io, big_endian=big_endian, tags=tags)
        self.bind(memory, offset)
        return self

    def bind_to_file(self, filepath: str, offset: int = 0, big_endian: bool = None, tags: Iterable[any] = (), through_memory=True):
        if self._flat:
            raise ValueError("Cannot bind a flattened struct to memory")
        
        io = None
        if through_memory:
            file_content = Path(filepath).read_bytes()
            io = BytesIO(file_content)
        else:
            io = open(filepath, "rb")
        self.bind_to_io(io, offset, big_endian, tags)
        return self
    
    def __enter__(self):
        if self._memory is None:
            raise ValueError("Struct is not bound to memory")
        self._memory.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        if self._memory is None:
            raise ValueError("Struct is not bound to memory")
        self._memory.__exit__(exc_type, exc_value, traceback)
        self._memory = None
        self._address = 0

    def read(self, memory: VirtualMemory, offset: int):
        if self._flat:
            raise ValueError("Cannot call read() on a flattened struct")
        struct_instance = self.__class__()
        struct_instance.bind(memory, offset)
        return struct_instance

    def flatten_type(self, memory: VirtualMemory = None, offset: int = None):
        if memory is None and offset is None:
            memory = self._memory
            offset = self._address
            
        flat_data = self.FLAT_TYPE()

        for key, field in self.FIELDS.items():
            if not self._is_field_active(key, memory):
                continue
            field_offset = offset + field.field_offset
            value = field.field_type.flatten_type(memory, field_offset)
            flat_data[key] = value

        flat_data._flat = True

        return flat_data
    
    def _is_field_active(self, field_key: str, memory: VirtualMemory):
        if field_key not in self._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS:
            return True
        
        modifier = self._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS[field_key]
        tags = memory._get_tags()
        return modifier.is_active(tags)
    
    @classmethod
    def _build_simple_property(cls, key, field):
        def getter(self):
            return field.read(self._memory, self._address + field.field_offset)
        
        def setter(self, value):
            return field.write(self._memory, self._address + field.field_offset, value)
        
        return property(getter, setter)
    
    @classmethod
    def _build_tag_dependant_property(cls, key, field):
        def process_tags(struct: Struct):
            memory = struct._memory
            tags = memory._get_tags()
            tag_modifier = cls._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS[key]
            if not tag_modifier.is_active(tags):
                raise ValueError(f"Cannot access field '{key}' because its tag modifier '{tag_modifier}' is not active (tags: {tags})")

        def getter(self: Struct):
            process_tags(self)
            return field.read(self._memory, self._address + field.field_offset)
        
        def setter(self: Struct, value):
            process_tags(self)
            return field.write(self._memory, self._address + field.field_offset, value)
        
        return property(getter, setter)

    @classmethod
    def _get_property_for_field(cls, key, field):
        if key in cls._FIELDS_DEPENDANT_ON_FIELD_MODIFIERS:
            return cls._build_tag_dependant_property(key, field)
        else:
            return cls._build_simple_property(key, field)