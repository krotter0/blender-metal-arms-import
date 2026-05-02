import struct, math

class BinaryReaderDetour:
    def __init__(self, reader, position):
        self.__reader = reader
        self.__oldPos = reader.tell()
        self.position = position
        
    def __enter__(self):
        self.__reader.seek(self.position)

    def __exit__(self, exc_type, exc_value, traceback):
        self.__reader.seek(self.__oldPos)

class BinaryReader:
    def __init__(self, filename, bigEndian):
        self.filename = filename
        self.endiannessPrefix = bigEndian and ">" or "<"
        self.offset = 0

    def __enter__(self):
        self.file = open(self.filename, "rb")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

    def _readFormatAll(self, format):
        format = self.endiannessPrefix + format
        buffer = self.file.read(struct.calcsize(format))
        return struct.unpack(format, buffer)

    def _readFormat(self, format):
        return self._readFormatAll(format)[0]
        
    def seek(self, position):
        self.file.seek(position + self.offset)
        
    def tell(self):
        return self.file.tell() - self.offset
        
    def applyPad(self, pad):
        currPos = self.tell()
        targetPos = math.ceil(currPos / 16) * 16
        self.seek(targetPos)
        
    def setOffset(self, offset):
        self.offset = offset
        
    def detour(self, position):
        return BinaryReaderDetour(self, position)

    def readPtrObject(self, object):
        ptr = self.readU32()
        if ptr == 0:
            return
        previousPos = self.tell()
        self.seek(ptr)
        
        object.read(self)
        
        self.seek(previousPos)
        return ptr

    def readPtrObjects(self, objects, stride=0):
        ptr = self.readU32()
        if ptr == 0:
            return
        previousPos = self.tell()
        self.seek(ptr)
        
        for object in objects:
            object.read(self)
            if stride > 0:
                ptr += stride
                self.seek(ptr)
        
        self.seek(previousPos)
        
    def skip(self, bytes):
        self.file.seek(self.file.tell() + bytes)
    
    def readBOOL8(self): return self.readU8() != 0
    def readBOOL(self): return self.readU32() != 0

    def readS8(self): return self._readFormat("b")
    def readU8(self): return self._readFormat("B")
    def readS16(self): return self._readFormat("h")
    def readU16(self): return self._readFormat("H")
    def readS32(self): return self._readFormat("i")
    def readU32(self): return self._readFormat("I")
    def readS64(self): return self._readFormat("q")
    def readU64(self): return self._readFormat("Q")
    def readF32(self): return self._readFormat("f")
    def readF64(self): return self._readFormat("d")
    def readChar(self): return self._readFormat("c")

    def readS8s(self, count): return self._readFormatAll("b" * count)
    def readU8s(self, count): return self._readFormatAll("B" * count)
    def readS16s(self, count): return self._readFormatAll("h" * count)
    def readU16s(self, count): return self._readFormatAll("H" * count)
    def readS32s(self, count): return self._readFormatAll("i" * count)
    def readU32s(self, count): return self._readFormatAll("I" * count)
    def readS64s(self, count): return self._readFormatAll("q" * count)
    def readU64s(self, count): return self._readFormatAll("Q" * count)
    def readF32s(self, count): return self._readFormatAll("f" * count)
    def readF64s(self, count): return self._readFormatAll("d" * count)
    def readChars(self, count): return self._readFormatAll("c" * count)
    
    def readString(self, length=None):
        if length == None:
            # Read as null-term string
            read = self.readChar()
            result = []
            while read != b"\x00":
                result.append(read)
                read = self.readChar()
                    
            if len(result) == 0:
                return ""
                
            string = b"".join(result)
            return string.decode("ascii")
        else:
            # Read as char array
            string = self._readFormat(str(length) + "s")
            string = string[:string.index(0)]
            return string.decode("ascii")

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
        
    def mulPoint(self, vec):
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
        self.x, self.y, self.z = reader.readF32s(3)
        
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
        self.x, self.y, self.z, self.a = reader.readF32s(4)
        
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
        self.x, self.y = reader.readF32s(2)
        
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
        self.r, self.g, self.b = reader.readF32s(3)
        
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
        
class CFSphere:
    def __init__(self):
        self.radius = 0.0
        self.pos = CFVec3()
    
    def read(self, reader: BinaryReader):
        self.radius = reader.readF32()
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
        self.x, self.y, self.z, self.a = reader.readF32s(4)
        
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