from enum import Enum

class Platform(Enum):
    DX = 0
    GC = 1
    DX_BETA = 2

    def is_big_endian(self):
        return self == Platform.GC

    @staticmethod
    def parse(value):
        if value == "DX":
            return Platform.DX
        if value == "DX_BETA":
            return Platform.DX_BETA
        elif value == "GC":
            return Platform.GC
        else:
            raise ValueError(f"Unknown platform: {value}")