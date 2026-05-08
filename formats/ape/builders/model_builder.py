import bpy
from ....formats.common.reader import CFVec3A
from ..reader import Ape
from . import skeleton_builder
from ....common import vec

class ModelBuildOptions:
    def __init__(self):
        self.filepath: str = ""
        self.lod_index: int = None
        self.create_armature: bool = True
        self.merge_clusters: bool = False
        self.parent: bpy.types.Object = None
        self.name: str = None

def _trilist_to_faces(ib, trilist, vb_offset):
    return [(ib[i] + vb_offset, ib[i+1] + vb_offset, ib[i+2] + vb_offset) for i in range(trilist.nStartVindex, trilist.nStartVindex + trilist.nTriCount * 3, 3)]

def _tristrip_to_faces(ib, tristrip, vb_offset):
    faces = []
    start = tristrip.nStartVindex
    end = tristrip.nStartVindex + tristrip.nTriCount

    for i in range(start, end):
        i0 = ib[i] + vb_offset
        i1 = ib[i + 1] + vb_offset
        i2 = ib[i + 2] + vb_offset

        # Triangle strips alternate winding every step
        if (i - start) % 2 == 0:
            face = (i0, i1, i2)
        else:
            face = (i1, i0, i2)

        # Skip degenerate triangles
        if face[0] == face[1] or face[1] == face[2] or face[0] == face[2]:
            continue

        faces.append(face)

    return faces

def _get_vb_verts(vb):
    x = int(vb.info.nOffsetPos/4)
    y = x + 1
    z = x + 2
    
    return [(vert[x], vert[z], vert[y]) for vert in vb.vb]

def _get_vb_normals(vb):
    if vb.info.nNormalCount <= 0:
        return [() for vert in vb.vb]
    
    x = int(vb.info.nOffsetNorm/4)
    y = x + 1
    z = x + 2
    
    return [(vert[x], vert[z], vert[y]) for vert in vb.vb]

def _transform_normal_by_bone_mtx(normal, mtx):
    x = mtx.x.x * normal[0] + mtx.z.x * normal[1] + mtx.y.x * normal[2]
    y = mtx.x.z * normal[0] + mtx.z.z * normal[1] + mtx.y.z * normal[2]
    z = mtx.x.y * normal[0] + mtx.z.y * normal[1] + mtx.y.y * normal[2]
    return vec.norm((x, y, z))

def _get_vb_uvs(vb):
    if vb.info.nTCCount <= 0:
        return [() for vert in vb.vb]
    
    u = int(vb.info.nOffsetTC/4)
    v = u + 1
        
    return [(vert[u], -vert[v]) for vert in vb.vb]

def _apply_cluster_obj_material(mtl, obj):
    mat_name = mtl.textureName
    if mat_name in obj.data.materials:
        return
    
    for material in bpy.data.materials:
        if material.name == mat_name:
            obj.data.materials.append(material)
            return
    
    material = bpy.data.materials.new(mtl.textureName)
    obj.data.materials.append(material)

def _compact_mesh_data(verts, uvs, normals, faces):
    used_indices = set()
    valid_faces = []

    for face in faces:
        if len(face) != 3:
            continue

        i0, i1, i2 = face
        if i0 == i1 or i1 == i2 or i0 == i2:
            continue

        if i0 < 0 or i1 < 0 or i2 < 0:
            continue

        if i0 >= len(verts) or i1 >= len(verts) or i2 >= len(verts):
            continue

        valid_faces.append((i0, i1, i2))
        used_indices.update((i0, i1, i2))

    if len(used_indices) == len(verts):
        return verts, uvs, normals, valid_faces

    index_map = {old_index: new_index for new_index, old_index in enumerate(sorted(used_indices))}

    compact_verts = [verts[old_index] for old_index in sorted(used_indices)]
    compact_uvs = [uvs[old_index] if old_index < len(uvs) else () for old_index in sorted(used_indices)]
    compact_normals = [normals[old_index] if old_index < len(normals) else () for old_index in sorted(used_indices)]
    compact_faces = [
        (index_map[i0], index_map[i1], index_map[i2])
        for i0, i1, i2 in valid_faces
    ]

    return compact_verts, compact_uvs, compact_normals, compact_faces

def _build_cluster(ape: Ape, mtl, cluster, armature_object=None, parent=None):
    vb_total_offsets = 0
    vb_offsets = []
    
    verts = []
    faces = []
    uvs = []
    normals = []
    
    for vb in ape.meshIS.vb:
        vb_offsets.append(vb_total_offsets)
        verts = verts + _get_vb_verts(vb)
        uvs = uvs + _get_vb_uvs(vb)
        normals = normals + _get_vb_normals(vb)
        
        vb_total_offsets = vb_total_offsets + len(vb.vb)
    
    name = ape.name
    seg = ape.seg[cluster.nSegmentIdx]
    if seg.boneMtxCount > 0:
        bone = ape.boneArray[seg.boneMtxIndexes[0]]
        name = bone.name
        mtx = bone.AtRestBoneToModelMtx
        for i, vert in enumerate(verts):
            vector = CFVec3A(vert[0], vert[2], vert[1])
            mtx.mul_point(vector)
            verts[i] = (vector.x, vector.z, vector.y)
        for i, normal in enumerate(normals):
            if len(normal) == 3:
                normals[i] = _transform_normal_by_bone_mtx(normal, mtx)
        
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    collection = bpy.context.collection
    collection.objects.link(obj)
    
    vb = ape.meshIS.vb[cluster.nVBIndex]
    ib = ape.meshIS.indicies[cluster.nIBIndex]
    
    vb_offset = vb_offsets[cluster.nVBIndex]
    
    faces = _trilist_to_faces(ib, cluster.TriList, vb_offset)
    for strip in cluster.StripBuffers:
        faces = faces + _tristrip_to_faces(ib, strip, vb_offset)
        
    verts, uvs, normals, faces = _compact_mesh_data(verts, uvs, normals, faces)

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    uv_layer = mesh.uv_layers.new(name="UVMap")

    for poly in mesh.polygons:
        poly.use_smooth = True
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            vert_uvs = uvs[vertex_index]
            if len(vert_uvs) > 0:
                uv_layer.data[loop_index].uv = vert_uvs

    if vb.info.nNormalCount > 0:
        loop_normals = [normals[loop.vertex_index] for loop in mesh.loops]
        mesh.normals_split_custom_set(loop_normals)
    
    _apply_cluster_obj_material(mtl, obj)

    if armature_object is not None:
        obj.parent = armature_object

        seg = ape.seg[cluster.nSegmentIdx]
        if seg.boneMtxCount > 0:
            bone_name = ape.boneArray[seg.boneMtxIndexes[0]].name
            vg = obj.vertex_groups.new(name=bone_name)
            vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')

        arm_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
        arm_mod.object = armature_object
    elif parent is not None:
        obj.parent = parent

    return obj

def build(ape: Ape, options: ModelBuildOptions = ModelBuildOptions()):
    armature_object = skeleton_builder.build(ape, options.name) if options.create_armature and ape.boneCount > 0 else None
    if armature_object is not None and options.parent is not None:
        armature_object.parent = options.parent

    clusters = []
    for mtl in ape.mtl:
        for cluster in mtl.platformData.clusters:
            if options.lod_index is not None and cluster.nLODID != options.lod_index:
                continue
            clusters.append(_build_cluster(ape, mtl, cluster, armature_object, options.parent))

    if options.merge_clusters and len(clusters) > 0:
        bpy.context.view_layer.objects.active = clusters[0]
        bpy.ops.object.select_all(action='DESELECT')
        for cluster in clusters:
            cluster.select_set(True)

        dest_obj = armature_object if armature_object is not None else clusters[0]
        merged_objs = [obj for obj in clusters if obj != dest_obj]
        with bpy.context.temp_override(active_object=dest_obj, selected_objects=merged_objs):
            bpy.ops.object.join()
        dest_obj.name = options.name or ape.name
        return dest_obj