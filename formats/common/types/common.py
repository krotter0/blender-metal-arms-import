from typing import Self

from ....common.binary_reader import BinaryReader

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