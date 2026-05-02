
from .common import BinaryReader, CFVec3, CFQuatA

FANIM_TRANSLATION_FRAC_BITS				= 8
FANIM_COMP_TRANSLATION_CONVERTER		= (1.0 / (1 << FANIM_TRANSLATION_FRAC_BITS))
FANIM_ORIENTATION_FRAC_BITS				= 14
FANIM_COMP_ORIENTATION_CONVERTER		= (1.0 / (1 << FANIM_ORIENTATION_FRAC_BITS))

class FAnimBone_t:
    def read(self, reader: BinaryReader):
        with reader.detour(reader.readU32()):
            self.name = reader.readString()
            
        self.sKeyCount = reader.readU16()
        self.tKeyCount = reader.readU16()
        self.oKeyCount = reader.readU16()
        reader.skip(2) #padding

        self.sKeyUnitTimePtr = reader.readU32()
        self.tKeyUnitTimePtr = reader.readU32()
        self.oKeyUnitTimePtr = reader.readU32()

        self.sKeyDataPtr = reader.readU32()
        self.tKeyDataPtr = reader.readU32()
        self.oKeyDataPtr = reader.readU32()

    def parseData(self, flags, totalSeconds, reader: BinaryReader):
        times_func = self._read_32bit_times
        if flags & 0x10:
            times_func = self._read_8bit_times
        elif flags & 0x20:
            times_func = self._read_16bit_times

        with reader.detour(self.sKeyUnitTimePtr):
            self.sKeyTimes = times_func(reader, self.sKeyCount, totalSeconds)
        with reader.detour(self.tKeyUnitTimePtr):
            self.tKeyTimes = times_func(reader, self.tKeyCount, totalSeconds)
        with reader.detour(self.oKeyUnitTimePtr):
            self.oKeyTimes = times_func(reader, self.oKeyCount, totalSeconds)

        with reader.detour(self.sKeyDataPtr):
            self._read_uncompressed_scalings(reader)

        with reader.detour(self.tKeyDataPtr):
            if flags & 0x1:
                self._read_compressed_translations(reader)
            else:
                self._read_uncompressed_translations(reader)

        with reader.detour(self.oKeyDataPtr):
            if flags & 0x2:
                self._read_compressed_orientations(reader)
            else:
                self._read_uncompressed_orientations(reader)

    def _read_8bit_times(self, reader: BinaryReader, count, totalSeconds):
        times = []
        for _ in range(count):
            times.append(reader.readU8() / 128.0 * totalSeconds)
        return times

    def _read_16bit_times(self, reader: BinaryReader, count, totalSeconds):
        times = []
        for _ in range(count):
            times.append(reader.readU16() / 32768.0 * totalSeconds)
        return times

    def _read_32bit_times(self, reader: BinaryReader, count, totalSeconds):
        times = []
        for _ in range(count):
            times.append(reader.readF32() * totalSeconds)
        return times

    def _read_uncompressed_scalings(self, reader: BinaryReader):
        self.sKeyData = []
        for _ in range(self.sKeyCount):
            self.sKeyData.append(reader.readF32())

    def _read_compressed_orientations(self, reader: BinaryReader):
        self.oKeyData = []
        for _ in range(self.oKeyCount):
            data = reader.readS16s(4)
            data = CFQuatA(data[0] * FANIM_COMP_ORIENTATION_CONVERTER, data[1] * FANIM_COMP_ORIENTATION_CONVERTER, data[2] * FANIM_COMP_ORIENTATION_CONVERTER, data[3] * FANIM_COMP_ORIENTATION_CONVERTER)
            self.oKeyData.append(data)

    def _read_uncompressed_orientations(self, reader: BinaryReader):
        self.oKeyData = []
        for _ in range(self.oKeyCount):
            data = CFQuatA()
            data.read(reader)
            self.oKeyData.append(data)

    def _read_compressed_translations(self, reader: BinaryReader):
        self.tKeyData = []
        for _ in range(self.tKeyCount):
            data = reader.readS16s(3)
            data = CFVec3(data[0] * FANIM_COMP_TRANSLATION_CONVERTER, data[1] * FANIM_COMP_TRANSLATION_CONVERTER, data[2] * FANIM_COMP_TRANSLATION_CONVERTER)
            self.tKeyData.append(data)

    def _read_uncompressed_translations(self, reader: BinaryReader):
        self.tKeyData = []
        for _ in range(self.tKeyCount):
            data = CFVec3()
            data.read(reader)
            self.tKeyData.append(data)

class Mtx:
    def __init__(self):
        pass
        
    def read(self, reader: BinaryReader):
        self.name = reader.readString(16)
        self.flags = reader.readU16()
        self.boneCount = reader.readU16()
        self.totalSeconds = reader.readF32()
        self.oTotalSeconds = reader.readF32()
        self.boneArray = [FAnimBone_t() for _ in range(self.boneCount)]
        reader.readPtrObjects(self.boneArray)
        for bone in self.boneArray:
            bone.parseData(self.flags, self.totalSeconds, reader)