from ....common.binary_reader import BinaryReader
from enum import Enum

class DataGameFileDataType(Enum):
    STRING = 0
    FLOAT = 1
    WIDESTRING = 2
    COUNT = 3

class FDataGamFile_Header_t:
    def __init__(self):
        self.bytes_in_file = 0
        self.tables = []
        self.flags = 0

    def read(self, reader: BinaryReader):
        self.bytes_in_file = reader.read_U32()
        num_tables = reader.read_U32()
        if num_tables > 10000:
            raise Exception(f"Number of tables is too high: {num_tables}")
        self.tables = [FDataGamFile_Table_t() for _ in range(num_tables)]
        reader.read_ptr_objects(self.tables)
        self.flags = reader.read_U32()

    def get_first_table_by_key(self, key: str):
        for table in self.tables:
            if table.name == key:
                return table
        return None

class FDataGamFile_Table_t:
    def __init__(self):
        self.name = ""
        self.table_index = 0
        self.fields: list[FDataGamFile_Field_t] = []

    def read(self, reader: BinaryReader):
        key_string_ptr = reader.read_U32()
        key_string_len = reader.read_U32()

        if key_string_len > 10000:
            raise Exception(f"Key string length is too high: {key_string_len}")
        
        with reader.detour(key_string_ptr):
            self.name = reader.read_string(key_string_len)

        num_fields = reader.read_U16()
        self.table_index = reader.read_U16()

        if num_fields > 10000:
            raise Exception(f"Number of fields is too high: {num_fields}")
        
        self.fields = [FDataGamFile_Field_t() for _ in range(num_fields)]
        reader.read_ptr_objects(self.fields)

class FDataGamFile_Field_t:
    def __init__(self):
        self.type = DataGameFileDataType.COUNT
        self.value = ""

    def read(self, reader: BinaryReader):
        self.type = DataGameFileDataType(reader.read_U32())
        if self.type == DataGameFileDataType.FLOAT:
            self.value = reader.read_F32()
            reader.skip(4)
        elif self.type == DataGameFileDataType.STRING or self.type == DataGameFileDataType.WIDESTRING:
            ptr = reader.read_U32()
            length = reader.read_U32()

            if length > 10000:
                raise Exception(f"Value string length is too high: {length}")
            
            if length == 0:
                self.value = ""
            else:
                with reader.detour(ptr):
                    if self.type == DataGameFileDataType.STRING:
                        self.value = reader.read_string(length)
                    else:
                        self.value = reader.read_widestring(length)

    def __str__(self):
        if self.type == DataGameFileDataType.FLOAT:
            return f"{self.value:.7g}"
        
        return str(self.value)