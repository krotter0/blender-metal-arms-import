import bpy
from . import material_builder
from  .model_builder_common import _build_segment_mesh_obj
from ....common.platform import Platform
from ....common import axis_convert
from ..types.model import Ape
from ..types.model_gc import FGCMesh_t, FGCMeshMaterial_t, FGC_DLCont_t, GXPrimitiveType

class ModelPrecomputeData:
    def __init__(self, ape: Ape):
        self.ape = ape
        self.meshes: list[list[bpy.types.Mesh]] = []

    def precompute(self):
        assert self.ape.platform == Platform.GC
        
        for mtl in self.ape.materials:
            display_list_meshes = []
            platform_data: FGCMeshMaterial_t = mtl.platform_data
            for dl_container in platform_data.dl_containers:
                dl_mesh = _build_displaylist_mesh(self.ape, mtl, dl_container)
                display_list_meshes.append(dl_mesh)
            self.meshes.append(display_list_meshes)

def _build_displaylist_mesh(ape: Ape, mtl: FGCMeshMaterial_t, dl_container: FGC_DLCont_t):
    name = ape.name
    gc_mesh: FGCMesh_t = ape.mesh_is
    primitives = dl_container.read_buffer(mtl, gc_mesh.vb)
    
    verts = []
    faces = []
    
    num_indices_added = 0
    vb = gc_mesh.vb[dl_container.vb_index]
    for prim in primitives:
        for i in range(prim.num_indices):
            pos_index = prim.pos_indices[i]
            pos_vertex = vb.vb[pos_index]
            
            vert = axis_convert.to_blender_pos(pos_vertex.pos)
            verts.append(vert)

        if prim.primitive_type == GXPrimitiveType.TRIANGLESTRIP:
            for i in range(prim.num_indices - 2):
                bi = num_indices_added + i
                if i % 2 == 0:
                    face = (bi, bi + 1, bi + 2)
                else:
                    face = (bi + 1, bi, bi + 2)
                faces.append(face)
        elif prim.primitive_type == GXPrimitiveType.TRIANGLES:
            for i in range(0, prim.num_indices, 3):
                bi = num_indices_added + i
                face = (bi, bi + 1, bi + 2)
                faces.append(face)
        num_indices_added += prim.num_indices
        
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh

def build_mesh_objs(precompute_data: ModelPrecomputeData, armature_object=None, parent=None, lod_filter=None):
    ape = precompute_data.ape
    assert ape.platform == Platform.GC

    dl_meshes = []
    for i, mtl in enumerate(ape.materials):
        blender_material = material_builder.build(ape, mtl)

        platform_data: FGCMeshMaterial_t = mtl.platform_data
        for j, dl in enumerate(platform_data.dl_containers):
            if lod_filter is not None and dl.lod_id != lod_filter:
                continue
            mesh = precompute_data.meshes[i][j]
            dl_meshes.append(_build_segment_mesh_obj(ape, mtl, dl.matrix_idx, mesh, blender_material, armature_object, parent))
    return dl_meshes