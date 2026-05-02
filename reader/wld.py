
from .ape import Ape
from .common import BinaryReader

class World:
    def read(self, reader: BinaryReader):
        self.nNumBytes = reader.readU32()
        self.nNumMeshes = reader.readU32()
        self.nOffsetToMeshInits = reader.readU32()
        self.nOffsetToMeshSizes = reader.readU32()
        self.nMeshBytes = reader.readU32()
        self.nWorldOffset = reader.readU32()
        self.nWorldBytes = reader.readU32()
        self.nStreamingDataOffset = reader.readU32()
        self.nStreamingDataBytes = reader.readU32()
        self.nInitOffsets = reader.readU32()
        self.nInitBytes = reader.readU32()
        
        oldPos = reader.tell()
        reader.seek(self.nOffsetToMeshInits)
        meshPointers = reader.readU32s(self.nNumMeshes)
        self.meshes = []
        for p in meshPointers:
            reader.seek(p)
            ape = Ape()
            reader.setOffset(p)
            ape.read(reader)
            reader.setOffset(0)
            self.meshes.append(ape)
            
        reader.setOffset(0)
        
        reader.seek(oldPos)