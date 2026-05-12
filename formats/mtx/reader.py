from ..common.types.common import CFVec3, CFQuatA
from ...common.binary_reader import BinaryReader

FANIM_TRANSLATION_FRAC_BITS      = 8
FANIM_COMP_TRANSLATION_CONVERTER = (1.0 / (1 << FANIM_TRANSLATION_FRAC_BITS))
FANIM_ORIENTATION_FRAC_BITS      = 14
FANIM_COMP_ORIENTATION_CONVERTER = (1.0 / (1 << FANIM_ORIENTATION_FRAC_BITS))

class FAnimBone_t:
    def __init__(self, anim):
        self.name = ""
        self._mtx_flags = anim.flags
        self._mtx_duration = anim.total_seconds

        self.scale_key_times: list[float] = []
        self.translation_key_times: list[float] = []
        self.orientation_key_times: list[float] = []
        self.scale_key_data: list[float] = []
        self.translation_key_data: list[CFVec3] = []
        self.orientation_key_data: list[CFQuatA] = []

    def read(self, reader: BinaryReader):
        with reader.detour(reader.read_U32()):
            self.name = reader.read_string()
            
        _scale_key_count = reader.read_U16()
        _translation_key_count = reader.read_U16()
        _orientation_key_count = reader.read_U16()
        reader.skip(2) #padding

        _scale_key_unit_time_ptr = reader.read_U32()
        _translation_key_unit_time_ptr = reader.read_U32()
        _orientation_key_unit_time_ptr = reader.read_U32()

        _scale_key_data_ptr = reader.read_U32()
        _translation_key_data_ptr = reader.read_U32()
        _orientation_key_data_ptr = reader.read_U32()

        times_func = self._read_32bit_times
        if self._mtx_flags & 0x10:
            times_func = self._read_8bit_times
        elif self._mtx_flags & 0x20:
            times_func = self._read_16bit_times

        with reader.detour(_scale_key_unit_time_ptr):
            self.scale_key_times = times_func(reader, _scale_key_count, self._mtx_duration)
        with reader.detour(_translation_key_unit_time_ptr):
            self.translation_key_times = times_func(reader, _translation_key_count, self._mtx_duration)
        with reader.detour(_orientation_key_unit_time_ptr):
            self.orientation_key_times = times_func(reader, _orientation_key_count, self._mtx_duration)

        with reader.detour(_scale_key_data_ptr):
            self._read_uncompressed_scalings(_scale_key_count, reader)

        with reader.detour(_translation_key_data_ptr):
            if self._mtx_flags & 0x1:
                self._read_compressed_translations(_translation_key_count, reader)
            else:
                self._read_uncompressed_translations(_translation_key_count, reader)

        with reader.detour(_orientation_key_data_ptr):
            if self._mtx_flags & 0x2:
                self._read_compressed_orientations(_orientation_key_count, reader)
            else:
                self._read_uncompressed_orientations(_orientation_key_count, reader)

    def _read_8bit_times(self, reader: BinaryReader, count, total_seconds: float):
        times = []
        for _ in range(count):
            times.append(reader.read_U8() / 128.0 * total_seconds)
        return times

    def _read_16bit_times(self, reader: BinaryReader, count, total_seconds: float):
        times = []
        for _ in range(count):
            times.append(reader.read_U16() / 32768.0 * total_seconds)
        return times

    def _read_32bit_times(self, reader: BinaryReader, count, total_seconds: float):
        times = []
        for _ in range(count):
            times.append(reader.read_F32() * total_seconds)
        return times

    def _read_uncompressed_scalings(self, count: int, reader: BinaryReader):
        self.scale_key_data = []
        for _ in range(count):
            self.scale_key_data.append(reader.read_F32())

    def _read_compressed_orientations(self, count: int, reader: BinaryReader):
        self.orientation_key_data = []
        for _ in range(count):
            data = reader.read_S16s(4)
            data = CFQuatA(data[0] * FANIM_COMP_ORIENTATION_CONVERTER, data[1] * FANIM_COMP_ORIENTATION_CONVERTER, data[2] * FANIM_COMP_ORIENTATION_CONVERTER, data[3] * FANIM_COMP_ORIENTATION_CONVERTER)
            self.orientation_key_data.append(data)

    def _read_uncompressed_orientations(self, count: int, reader: BinaryReader):
        self.orientation_key_data = []
        for _ in range(count):
            data = CFQuatA()
            data.read(reader)
            self.orientation_key_data.append(data)

    def _read_compressed_translations(self, count: int, reader: BinaryReader):
        self.translation_key_data = []
        for _ in range(count):
            data = reader.read_S16s(3)
            data = CFVec3(data[0] * FANIM_COMP_TRANSLATION_CONVERTER, data[1] * FANIM_COMP_TRANSLATION_CONVERTER, data[2] * FANIM_COMP_TRANSLATION_CONVERTER)
            self.translation_key_data.append(data)

    def _read_uncompressed_translations(self, count: int, reader: BinaryReader):
        self.translation_key_data = []
        for _ in range(count):
            data = CFVec3()
            data.read(reader)
            self.translation_key_data.append(data)

class Mtx:
    def __init__(self):
        self.name = ""
        self.flags = 0
        self.bone_count = 0
        self.total_seconds = 0.0
        self.bones: list[FAnimBone_t] = []
        
    def read(self, reader: BinaryReader):
        self.name = reader.read_string(16)
        self.flags = reader.read_U16()
        bone_count = reader.read_U16()
        self.total_seconds = reader.read_F32()
        inv_total_seconds = reader.read_F32()
        self.bones = [FAnimBone_t(self) for _ in range(bone_count)]
        reader.read_ptr_objects(self.bones)