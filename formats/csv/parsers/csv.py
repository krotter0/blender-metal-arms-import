from ..types.csv import FDataGamFile_Field_t, FDataGamFile_Header_t, DataGameFileDataType
from .models.csv import ParsedCSV

class CSVParser:
    def _parse_field(self, field: FDataGamFile_Field_t):
        if field.type == DataGameFileDataType.STRING:
            return field.string.deref
        elif field.type == DataGameFileDataType.WIDESTRING:
            return field.widestring.deref
        elif field.type == DataGameFileDataType.FLOAT:
            return field.float_value
        else:
            raise ValueError(f"Unknown data type {field.type} in CSV field")

    def parse(self, csv: FDataGamFile_Header_t) -> ParsedCSV:
        tables: dict[str, list[list[any]]] = {}
        for table in csv.tables:
            table_name = table.key_string_ptr.deref
            table_data = [self._parse_field(field) for field in table.fields]
            if table_name in tables:
                tables[table_name].append(table_data)
            else:
                tables[table_name] = [table_data]
        return ParsedCSV(tables)