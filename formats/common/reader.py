import struct, math
from typing import Self

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
    def __init__(self, filename, big_endian):
        self.filename = filename
        self._endianness_prefix = big_endian and ">" or "<"
        self.offset = 0

    def __enter__(self):
        self.file = open(self.filename, "rb")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

    def _read_format_all(self, format):
        format = self._endianness_prefix + format
        buffer = self.file.read(struct.calcsize(format))
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
                chunk = self.file.read(char_size)
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
        self.file.seek(position + self.offset)
        
    def tell(self):
        return self.file.tell() - self.offset
        
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

    def read_ptr_objects(self, objects, stride=0):
        ptr = self.read_U32()
        if ptr == 0:
            return
        previous_pos = self.tell()
        self.seek(ptr)
        
        for object in objects:
            object.read(self)
            if stride > 0:
                ptr += stride
                self.seek(ptr)
        
        self.seek(previous_pos)
        
    def skip(self, bytes):
        self.file.seek(self.file.tell() + bytes)
    
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

class CFMtx43A:
    def __init__(self):
        self.x = CFVec3A()
        self.y = CFVec3A()
        self.z = CFVec3A()
        self.a = CFVec3A()
    
    def read(self, reader: BinaryReader):
        self.x.read(reader)
        self.y.read(reader)
        self.z.read(reader)
        self.a.read(reader)
        
    def identity(self):
        self.x.x = 1.0
        self.y.y = 1.0
        self.z.z = 1.0
        
    def mul_point(self, vec):
        x = self.x.x*vec.x + self.y.x*vec.y + self.z.x*vec.z + self.a.x;
        y = self.x.y*vec.x + self.y.y*vec.y + self.z.y*vec.z + self.a.y;
        z = self.x.z*vec.x + self.y.z*vec.y + self.z.z*vec.z + self.a.z;
        vec.x = x
        vec.y = y
        vec.z = z
        
class CFMtx43:
    def __init__(self):
        self.x = CFVec3()
        self.y = CFVec3()
        self.z = CFVec3()
        self.a = CFVec3()
    
    def read(self, reader: BinaryReader):
        self.x.read(reader)
        self.y.read(reader)
        self.z.read(reader)
        self.a.read(reader)
        
    def identity(self):
        self.x.x = 1.0
        self.y.y = 1.0
        self.z.z = 1.0
        
    def mul_point(self, vec):
        x = self.x.x*vec.x + self.y.x*vec.y + self.z.x*vec.z + self.a.x;
        y = self.x.y*vec.x + self.y.y*vec.y + self.z.y*vec.z + self.a.y;
        z = self.x.z*vec.x + self.y.z*vec.y + self.z.z*vec.z + self.a.z;
        vec.x = x
        vec.y = y
        vec.z = z

class CFVec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def read(self, reader: BinaryReader):
        self.x, self.y, self.z = reader.read_F32s(3)
        
    def __repr__(self):
        return 'CFVec3(x={:.3f}, y={:.3f}, z={:.3f})'.format(self.x, self.y, self.z)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        else:
            raise IndexError("CFVec3 index out of range")

    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value
        else:
            raise IndexError("CFVec3 index out of range")

class CFVec3A:
    def __init__(self, x=0.0, y=0.0, z=0.0, a=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.a = a

    def read(self, reader: BinaryReader):
        self.x, self.y, self.z, self.a = reader.read_F32s(4)
        
    def __repr__(self):
        return 'CFVec3(x={:.3f}, y={:.3f}, z={:.3f}, a={:.3f})'.format(self.x, self.y, self.z, self.a)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError("CFVec3A index out of range")

    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value
        elif key == 3:
            self.a = value
        else:
            raise IndexError("CFVec3A index out of range")

class CFVec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def read(self, reader: BinaryReader):
        self.x, self.y = reader.read_F32s(2)
        
    def __repr__(self):
        return 'CFVec3(x={:.3f}, y={:.3f})'.format(self.x, self.y)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("CFVec2 index out of range")
        
    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("CFVec2 index out of range")


class CFColorRGB:
    def __init__(self):
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0

    def read(self, reader: BinaryReader):
        self.r, self.g, self.b = reader.read_F32s(3)
        
    def __repr__(self):
        return 'CFColorRGB(r={:.3f}, g={:.3f}, b={:.3f})'.format(self.r, self.g, self.b)
    
    def __getitem__(self, key):
        if key == 0:
            return self.r
        elif key == 1:
            return self.g
        elif key == 2:
            return self.b
        else:
            raise IndexError("CFColorRGB index out of range")
        
    def __setitem__(self, key, value):
        if key == 0:
            self.r = value
        elif key == 1:
            self.g = value
        elif key == 2:
            self.b = value
        else:
            raise IndexError("CFColorRGB index out of range")
        
class CFColorRGBA:
    def __init__(self):
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0
        self.a = 0.0

    def read(self, reader: BinaryReader):
        self.r, self.g, self.b, self.a = reader.read_F32s(4)
        
    def __repr__(self):
        return 'CFColorRGBA(r={:.3f}, g={:.3f}, b={:.3f}, a={:.3f})'.format(self.r, self.g, self.b, self.a)
    
    def __getitem__(self, key):
        if key == 0:
            return self.r
        elif key == 1:
            return self.g
        elif key == 2:
            return self.b
        elif key == 3:
            return self.a
        else:
            raise IndexError("CFColorRGBA index out of range")
        
    def __setitem__(self, key, value):
        if key == 0:
            self.r = value
        elif key == 1:
            self.g = value
        elif key == 2:
            self.b = value
        elif key == 3:
            self.a = value
        else:
            raise IndexError("CFColorRGBA index out of range")
        
class CFSphere:
    def __init__(self):
        self.radius = 0.0
        self.pos = CFVec3()
    
    def read(self, reader: BinaryReader):
        self.radius = reader.read_F32()
        self.pos.read(reader)
        
    def __repr__(self):
        return 'CFSphere(radius={:.3f}, pos={})'.format(self.radius, self.pos)
    
class CFQuatA:
    def __init__(self, x=0.0, y=0.0, z=0.0, a=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.a = a

    def read(self, reader: BinaryReader):
        self.x, self.y, self.z, self.a = reader.read_F32s(4)
        
    def __repr__(self):
        return 'CFQuatA(x={:.3f}, y={:.3f}, z={:.3f}, a={:.3f})'.format(self.x, self.y, self.z, self.a)
    
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        elif key == 3:
            return self.a
        else:
            raise IndexError("CFQuatA index out of range")
        
    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value
        elif key == 3:
            self.a = value
        else:
            raise IndexError("CFQuatA index out of range")
        
class CFColorMotif(CFColorRGBA):
    def __init__(self):
        super().__init__()
        self.motif_index = 0

    def read(self, reader: BinaryReader):
        super().read(reader)
        self.motif_index = reader.read_U32()

class FLinkRoot_s:
    def __init__(self):
        self.head_link: FLink_t = None
        self.tail_link: FLink_t = None
        self.struct_offset = 0
        self.struct_size = 0

    def read(self, reader: BinaryReader):
        ptrs = {}
        self._read(reader, ptrs)

    def _read(self, reader: BinaryReader, ptrs: dict[int, Self]):
        self.head_link = FLink_t._read_one(reader, ptrs)
        self.tail_link = FLink_t._read_one(reader, ptrs)

        self.struct_offset = reader.read_U32()
        self.struct_size = reader.read_U32()

    def _read_one_link(self, reader: BinaryReader, ptrs: dict[int, Self]):
        ptr = reader.read_U32()
        if ptr == 0:
            return None
        elif ptr in ptrs:
            return ptrs[ptr]

        obj = FLink_t()
        ptrs[ptr] = obj

        with reader.detour(ptr):
            obj._read(reader, ptrs)
        return obj
    
    @staticmethod
    def read_multiple(reader: BinaryReader, count: int):
        ptrs = {}
        roots = []
        for _ in range(count):
            root = FLinkRoot_s()
            root._read(reader, ptrs)
            roots.append(root)
        return roots

class FLink_t:
    def __init__(self):
        self.prev_link: FLink_t = None
        self.next_link: FLink_t = None

    def read(self, reader: BinaryReader):
        self._read(reader, {})

    def _read(self, reader: BinaryReader, ptrs: dict[int, Self]):
        self.prev_link = FLink_t._read_one(reader, ptrs)
        self.next_link = FLink_t._read_one(reader, ptrs)

    @staticmethod
    def _read_one(reader: BinaryReader, ptrs: dict[int, Self]):
        ptr = reader.read_U32()
        if ptr == 0:
            return None
        elif ptr in ptrs:
            return ptrs[ptr]

        obj = FLink_t()
        ptrs[ptr] = obj

        with reader.detour(ptr):
            obj._read(reader, ptrs)
        return obj