import bpy
from ..types.model import Ape, FMeshMaterial_t

def _build_segment_mesh_obj(ape: Ape, mtl: FMeshMaterial_t, mtx_idx: int | None, mesh, blender_material, armature_object=None, parent=None):
    name = ape.name
    obj = bpy.data.objects.new(name, mesh)
    
    collection = bpy.context.collection
    collection.objects.link(obj)

    obj.data.materials.append(blender_material)

    if armature_object is not None:
        obj.parent = armature_object

        if mtx_idx is not None:
            bone_name = ape.bones[mtx_idx].name
            vg = obj.vertex_groups.new(name=bone_name)
            vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')

        arm_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
        arm_mod.object = armature_object
    elif parent is not None:
        obj.parent = parent

    return obj