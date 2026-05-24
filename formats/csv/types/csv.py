from enum import Enum
from ....structs.field import *
from ....structs.fieldtype import *
from ....structs.structs import *
from ....structs.virtualmemory import *
from ...common.types.common import *

class DataGameFileDataType(Enum):
    STRING = 0
    FLOAT = 1
    WIDESTRING = 2
    COUNT = 3

class FDataGamFile_Field_t(Struct):
    type: DataGameFileDataType = Field(EnumType(DataGameFileDataType, 4))
    BeginUnion()
    string: Pointer[NullTermString] = PointerTo(NullTermString())
    widestring: Pointer[NullTermString] = PointerTo(NullTermString(wide=True))
    float_value: float = Field(f32)
    EndUnion()
    string_len: int = Field(u32)

class FDataGamFile_Table_t(Struct):
    key_string_ptr: Pointer[NullTermString] = PointerTo(NullTermString())
    key_string_len: int = Field(u32)
    num_fields: int = Field(u16)
    table_index: int = Field(u16)
    fields: IterablePointer[FDataGamFile_Field_t] = IterablePointerField(FDataGamFile_Field_t, "num_fields")

class FDataGamFile_Header_t(Struct):
    bytes_in_file: int = Field(u32)
    num_tables: int = Field(u32)
    tables: IterablePointer[FDataGamFile_Table_t] = IterablePointerField(FDataGamFile_Table_t, "num_tables")
    flags: int = Field(u32)