from io import BytesIO, IOBase
from pathlib import Path
import struct, math

class _BinaryReaderDetour:
    def __init__(self, reader, position: int, set_offset: bool=False):
        self._reader = reader
        self._old_pos = reader.tell()
        self._set_offset = set_offset
        self._old_offset = reader.offset
        self.position = position
        
    def __enter__(self):
        if self._set_offset:
            self._reader.set_offset(self.position + self._reader.offset)
            self._reader.seek(0)
        else:
            self._reader.seek(self.position)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._set_offset:
            self._reader.set_offset(self._old_offset)
        self._reader.seek(self._old_pos)

class BinaryReader:
    def __init__(self, source: str | IOBase | bytes | Path, big_endian, close_on_exit=True):
        self.source = source
        self._endianness_prefix = big_endian and ">" or "<"
        self.offset = 0
        self._close_on_exit = close_on_exit or not isinstance(source, IOBase)

    def __enter__(self):
        if isinstance(self.source, str):
            self.io = open(self.source, "rb")
        elif isinstance(self.source, Path):
            self.io = open(self.source, "rb")
        elif isinstance(self.source, bytes):
            self.io = BytesIO(self.source)
        else:
            self.io = self.source
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._close_on_exit:
            self.io.close()

    def _read_format_all(self, format):
        format = self._endianness_prefix + format
        buffer = self.io.read(struct.calcsize(format))
        return list(struct.unpack(format, buffer))

    def _read_format(self, format):
        return self._read_format_all(format)[0]
    
    def _read_string(self, wide, length=None):
        encoding = "utf-16-le" if wide else "ascii"
        char_size = 2 if wide else 1

        if length is None:
            # Read as null-term string
            result = []
            while True:
                chunk = self.io.read(char_size)
                if chunk == b"\x00" * char_size:
                    break
                result.append(chunk)

            if not result:
                return ""

            return b"".join(result).decode(encoding)
        else:
            # Read as char array
            string = self._read_format(str(length * char_size) + "s")
            null_term = string.find(b"\x00" * char_size)
            if null_term != -1:
                string = string[:null_term]
            return string.decode(encoding)
        
    def seek(self, position):
        self.io.seek(position + self.offset)
        
    def tell(self):
        return self.io.tell() - self.offset
        
    def apply_pad(self, pad):
        curr_pos = self.tell()
        target_pos = math.ceil(curr_pos / 16) * 16
        self.seek(target_pos)
        
    def set_offset(self, offset):
        self.offset = offset
        
    def detour(self, position, set_offset=False):
        return _BinaryReaderDetour(self, position, set_offset)

    def read_ptr_object(self, object):
        ptr = self.read_U32()
        if ptr == 0:
            return
        previous_pos = self.tell()
        self.seek(ptr)
        
        object.read(self)
        
        self.seek(previous_pos)
        return ptr

    def read_ptr_objects(self, objects, stride=None):
        ptr = self.read_U32()
        if ptr == 0:
            return
        previous_pos = self.tell()
        self.seek(ptr)
        
        for object in objects:
            object.read(self)
            if stride is not None:
                ptr += stride
                self.seek(ptr)
        
        self.seek(previous_pos)
        
    def skip(self, bytes):
        self.io.seek(self.io.tell() + bytes)
    
    def read_BOOL8(self): return self.read_U8() != 0
    def read_BOOL(self): return self.read_U32() != 0

    def read_S8(self): return self._read_format("b")
    def read_U8(self): return self._read_format("B")
    def read_S16(self): return self._read_format("h")
    def read_U16(self): return self._read_format("H")
    def read_S32(self): return self._read_format("i")
    def read_U32(self): return self._read_format("I")
    def read_S64(self): return self._read_format("q")
    def read_U64(self): return self._read_format("Q")
    def read_F32(self): return self._read_format("f")
    def read_F64(self): return self._read_format("d")
    def read_Char(self): return self._read_format("c")

    def read_S8s(self, count): return self._read_format_all("b" * count)
    def read_U8s(self, count): return self._read_format_all("B" * count)
    def read_S16s(self, count): return self._read_format_all("h" * count)
    def read_U16s(self, count): return self._read_format_all("H" * count)
    def read_S32s(self, count): return self._read_format_all("i" * count)
    def read_U32s(self, count): return self._read_format_all("I" * count)
    def read_S64s(self, count): return self._read_format_all("q" * count)
    def read_U64s(self, count): return self._read_format_all("Q" * count)
    def read_F32s(self, count): return self._read_format_all("f" * count)
    def read_F64s(self, count): return self._read_format_all("d" * count)
    def read_Chars(self, count): return self._read_format_all("c" * count)

    def read_string(self, length=None):
        return self._read_string(False, length)
    
    def read_widestring(self, length=None):
        return self._read_string(True, length)
    
    def read_binary(self, length):
        return self.io.read(length)