from dataclasses import dataclass

@dataclass
class ParsedCSV:
    tables: dict[str, list[list[any]]]

    def get_first_table_by_key(self, key: str):
        for table_name, table in self.tables.items():
            if table_name == key:
                return table[0] if len(table) > 0 else None
        return None