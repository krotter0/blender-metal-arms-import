import bpy
from .model_builder_common import _build_segment_mesh_obj
from ....common.platform import Platform
from ....common import vec
from ...common.types.common import CFVec3A
from ..types.model import Ape, FMeshMaterial_t
from ..types.model_dx8 import FDX8MeshCluster_t, FDX8MeshMaterial_t, FDX8MeshStrip_t, FDX8MeshTriList_t
from . import material_builder 

class ModelPrecomputeData:
    def __init__(self, ape: Ape):
        self.ape = ape
        self.meshes: list[list[bpy.types.Mesh]] = []

    def precompute(self):
        assert self.ape.platform == Platform.DX
        
        for mtl in self.ape.materials:
            cluster_meshes = []
            platform_data: FDX8MeshMaterial_t = mtl.platform_data
            for cluster in platform_data.clusters:
                cluster_mesh = _build_cluster_mesh(self.ape, cluster)
                cluster_meshes.append(cluster_mesh)
            self.meshes.append(cluster_meshes)

def _trilist_to_faces(ib: list[int], trilist: FDX8MeshTriList_t, vb_offset: int):
    return [(ib[i] + vb_offset, ib[i+1] + vb_offset, ib[i+2] + vb_offset) for i in range(trilist.start_vindex, trilist.start_vindex + trilist.tri_count * 3, 3)]

def _tristrip_to_faces(ib: list[int], tristrip: FDX8MeshStrip_t, vb_offset: int):
    faces = []
    start = tristrip.start_vindex
    end = tristrip.start_vindex + tristrip.tri_count

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

def _transform_normal_by_bone_mtx(normal, mtx):
    x = mtx.x.x * normal[0] + mtx.z.x * normal[1] + mtx.y.x * normal[2]
    y = mtx.x.z * normal[0] + mtx.z.z * normal[1] + mtx.y.z * normal[2]
    z = mtx.x.y * normal[0] + mtx.z.y * normal[1] + mtx.y.y * normal[2]
    return vec.norm((x, y, z))

def _compact_mesh_data(verts, uvs, normals, colors, faces):
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
        return verts, uvs, normals, colors, valid_faces

    index_map = {old_index: new_index for new_index, old_index in enumerate(sorted(used_indices))}

    compact_verts = [verts[old_index] for old_index in sorted(used_indices)]
    compact_uvs = [uvs[old_index] if old_index < len(uvs) else () for old_index in sorted(used_indices)]
    compact_colors = [colors[old_index] if old_index < len(colors) else () for old_index in sorted(used_indices)]
    compact_normals = [normals[old_index] if old_index < len(normals) else () for old_index in sorted(used_indices)]
    compact_faces = [
        (index_map[i0], index_map[i1], index_map[i2])
        for i0, i1, i2 in valid_faces
    ]

    return compact_verts, compact_uvs, compact_normals, compact_colors, compact_faces

def _build_cluster_mesh(ape: Ape, cluster: FDX8MeshCluster_t):
    vb_total_offsets = 0
    vb_offsets = []
    
    verts = []
    faces = []
    uvs = []
    normals = []
    colors = []
    
    for vb in ape.mesh_is.vb:
        vb_offsets.append(vb_total_offsets)

        for vertex in vb.vb:
            verts.append((vertex.pos[0], vertex.pos[2], vertex.pos[1]))
            uvs.append([(uv[0], -uv[1]) for uv in vertex.uvs])
            normals.append([(x[0], x[2], x[1]) for x in vertex.normals])
            colors.append([(x[2], x[1], x[0], x[3]) for x in vertex.colors])
        
        vb_total_offsets = vb_total_offsets + len(vb.vb)
    
    name = ape.name
    seg = ape.segs[cluster.segment_idx]
    if seg.bone_mtx_count > 0:
        bone = ape.bones[seg.bone_mtx_indices[0]]
        name = bone.name
        mtx = bone.at_rest_bone_to_model_mtx
        for i, vert in enumerate(verts):
            vector = CFVec3A(vert[0], vert[2], vert[1])
            mtx.mul_point(vector)
            verts[i] = (vector.x, vector.z, vector.y)
        for i, normal_group in enumerate(normals):
            for j, normal in enumerate(normal_group):
                normals[i][j] = _transform_normal_by_bone_mtx(normal, mtx)
    
    vb = ape.mesh_is.vb[cluster.vb_index]
    ib = ape.mesh_is.indices[cluster.ib_index]
    
    vb_offset = vb_offsets[cluster.vb_index]
    
    faces = _trilist_to_faces(ib, cluster.tri_list, vb_offset)
    for strip in cluster.strip_buffers:
        faces = faces + _tristrip_to_faces(ib, strip, vb_offset)
        
    verts, uvs, normals, colors, faces = _compact_mesh_data(verts, uvs, normals, colors, faces)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    for uv_index in range(vb.info.tc_count):
        uv_layer = mesh.uv_layers.new(name=f"uv_{uv_index}")

        for poly in mesh.polygons:
            poly.use_smooth = True
            for loop_index in poly.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                vert_uvs = uvs[vertex_index]
                if len(vert_uvs) > 0:
                    u = vert_uvs[uv_index][0]
                    v = vert_uvs[uv_index][1]
                    uv_layer.data[loop_index].uv = (u, v)

    if vb.info.normal_count > 0:
        loop_normals = [normals[loop.vertex_index][0] for loop in mesh.loops]
        mesh.normals_split_custom_set(loop_normals)

    for channel_index in range(vb.info.color_count):
        color_layer = mesh.vertex_colors.new(name=f"color_{channel_index}")
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                vert_colors = colors[vertex_index][channel_index]
                color_layer.data[loop_index].color = vert_colors

    return mesh

def build_mesh_objs(precompute_data: ModelPrecomputeData, armature_object=None, parent=None, lod_filter=None):
    ape = precompute_data.ape
    assert ape.platform == Platform.DX

    clusters = []
    for i, mtl in enumerate(ape.materials):
        blender_material = material_builder.build(ape, mtl)

        platform_data: FDX8MeshMaterial_t = mtl.platform_data
        for j, cluster in enumerate(platform_data.clusters):
            if lod_filter is not None and cluster.lod_id != lod_filter:
                continue
            mesh = precompute_data.meshes[i][j]
            
            segment = ape.segs[cluster.segment_idx]
            mtx_idx = segment.bone_mtx_indices[0] if segment.bone_mtx_count > 0 else None
            clusters.append(_build_segment_mesh_obj(ape, mtl, mtx_idx, mesh, blender_material, armature_object, parent))
    return clusters