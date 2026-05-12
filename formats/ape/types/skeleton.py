from ...common.types.common import CFMtx43A, CFSphere
from ....common.binary_reader import BinaryReader

class FMeshSkeleton_t:
    def __init__(self):
        self.parent_bone_index = 0
        self.child_bone_count = 0
        self.child_array_start_index = 0

    def read(self, reader: BinaryReader):
        self.parent_bone_index = reader.read_U8()
        self.child_bone_count = reader.read_U8()
        self.child_array_start_index = reader.read_U8()

class FMeshBone_t:
    def __init__(self):
        self.name = ""

        self.at_rest_bone_to_model_mtx = CFMtx43A()
        self.at_rest_model_to_bone_mtx = CFMtx43A()
        self.at_rest_parent_to_bone_mtx = CFMtx43A()
        self.at_rest_bone_to_parent_mtx = CFMtx43A()
        
        self.segmented_bound_sphere_bs = CFSphere()
        self.skeleton = FMeshSkeleton_t()

        self.flags = 0
        self.part_id = 0
        
    def read(self, reader: BinaryReader):
        self.name = reader.read_string(32)
        
        self.at_rest_bone_to_model_mtx.read(reader)
        self.at_rest_model_to_bone_mtx.read(reader)
        self.at_rest_parent_to_bone_mtx.read(reader)
        self.at_rest_bone_to_parent_mtx.read(reader)
        
        self.segmented_bound_sphere_bs.read(reader)
        self.skeleton.read(reader)
        
        self.flags = reader.read_U8()
        self.part_id = reader.read_U8()
        reader.read_U8s(3) #PAD