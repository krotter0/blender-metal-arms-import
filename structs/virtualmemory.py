import struct
import sys
from io import IOBase
from collections.abc import Iterable

class EndiannessStruct:
    def __init__(self, format: str):
        self.big_endian = struct.Struct(">" + format)
        self.little_endian = struct.Struct("<" + format)
        self.size = self.big_endian.size
    
class VirtualMemory:
    def __init__(self, io: IOBase, big_endian:bool=None, offset:int=0, tags: Iterable[any] = ()):
        if big_endian is None:
            big_endian = sys.byteorder == "big"

        self.io = io
        self.big_endian = big_endian
        self._readable = self.io.seekable() and self.io.readable()
        self._writable = self.io.seekable() and self.io.writable()
        self._tags = set(tags)
        self._offset = offset
        assert self.io.seekable(), "VirtualMemory requires a seekable IO object"

    def _get_tags(self):
        return self._tags

    def readable(self):
        return self._readable
    
    def writable(self):
        return self._writable
    
    def read(self, size: int, offset: int = None):
        if offset is not None:
            self.io.seek(offset + self._offset)
        return self.io.read(size)
    
    def write(self, data: bytes, offset: int = None):
        if offset is not None:
            self.io.seek(offset + self._offset)
        self.io.write(data)

    def read_struct(self, struct: EndiannessStruct, offset: int = None):
        data = self.read(struct.size, offset)
        if self.big_endian:
            return struct.big_endian.unpack(data)
        else:
            return struct.little_endian.unpack(data)
        
    def write_struct(self, struct: EndiannessStruct, values: tuple, offset: int = None):
        if self.big_endian:
            data = struct.big_endian.pack(*values)
        else:
            data = struct.little_endian.pack(*values)
        self.write(data, offset)

    def copy(self, offset: int = 0):
        offset += self._offset
        return VirtualMemory(self.io, big_endian=self.big_endian, offset=offset, tags=self._tags)
    
    def set_offset(self, offset: int):
        self._offset = offset

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.io.close()

class VirtualMemoryBind:
    def __init__(self, memory: VirtualMemory, offset: int):
        self.memory = memory
        self.offset = offset