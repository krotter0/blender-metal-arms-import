import bpy
from ....formats.ape.builders import material_builder
import mathutils
from ...common.types.common import CFVec3A
from ..types.model import Ape, FDX8MeshCluster_t, FDX8MeshStrip_t, FDX8MeshTriList_t, FMeshMaterial_t
from . import skeleton_builder
from ....common import vec, axis_convert
from ....formats.common.builders import light_builder

class ModelBuildOptions:
    def __init__(self):
        self.filepath: str = ""
        self.lod_index: int = None
        self.create_armature: bool = True
        self.merge_clusters: bool = False
        self.parent: bpy.types.Object = None
        self.name: str = None
        self.texture_folder_path: str = None
        self.texture_allow_recurse: bool = True

class ModelPrecomputeData:
    def __init__(self, ape: Ape):
        self.ape = ape
        self.cluster_meshes: list[list[bpy.types.Mesh]] = []

    def precompute(self):
        for mtl in self.ape.materials:
            cluster_meshes = []
            for cluster in mtl.platform_data.clusters:
                cluster_mesh = _build_cluster_mesh(self.ape, cluster)
                cluster_meshes.append(cluster_mesh)
            self.cluster_meshes.append(cluster_meshes)

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

def _apply_cluster_obj_material(mtl: FMeshMaterial_t, obj: bpy.types.Object): #TODO: Remove
    mat_name = mtl.texture_name
    if mat_name in obj.data.materials:
        return
    
    for material in bpy.data.materials:
        if material.name == mat_name:
            obj.data.materials.append(material)
            return
    
    material = bpy.data.materials.new(mtl.texture_name)
    obj.data.materials.append(material)

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

def _build_cluster(ape: Ape, mtl: FMeshMaterial_t, cluster: FDX8MeshCluster_t, mesh, blender_material, armature_object=None, parent=None):
    name = ape.name
    obj = bpy.data.objects.new(name, mesh)
    
    collection = bpy.context.collection
    collection.objects.link(obj)

    #_apply_cluster_obj_material(mtl, obj)
    obj.data.materials.append(blender_material)

    if armature_object is not None:
        obj.parent = armature_object

        seg = ape.segs[cluster.segment_idx]
        if seg.bone_mtx_count > 0:
            bone_name = ape.bones[seg.bone_mtx_indices[0]].name
            vg = obj.vertex_groups.new(name=bone_name)
            vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')

        arm_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
        arm_mod.object = armature_object
    elif parent is not None:
        obj.parent = parent

    return obj

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

def build(ape: Ape, options: ModelBuildOptions = ModelBuildOptions()):
    precompute_data = ModelPrecomputeData(ape)
    precompute_data.precompute()
    return build_from_precompute(precompute_data, options)
    
def build_from_precompute(precompute_data: ModelPrecomputeData, options: ModelBuildOptions = ModelBuildOptions()):
    ape = precompute_data.ape
    armature_object = skeleton_builder.build(ape, options.name) if options.create_armature and len(ape.bones) > 0 else None
    if armature_object is not None and options.parent is not None:
        armature_object.parent = options.parent

    if options.texture_folder_path is not None:
        material_builder.build_textures_from_file_system(ape, options.texture_folder_path, options.texture_allow_recurse)
    clusters = []
    for i, mtl in enumerate(ape.materials):
        blender_material = material_builder.build(ape, mtl)
        for j, cluster in enumerate(mtl.platform_data.clusters):
            if options.lod_index is not None and cluster.lod_id != options.lod_index:
                continue
            mesh = precompute_data.cluster_meshes[i][j]
            clusters.append(_build_cluster(ape, mtl, cluster, mesh, blender_material, armature_object, options.parent))

    for i, light_init in enumerate(ape.lights):
        light = light_builder.build(i, light_init)
        if light_init.parent_bone_idx != -1 and armature_object is not None:
            bone = ape.bones[light_init.parent_bone_idx]
            
            bone_to_model_mtx = axis_convert.mtx43a_to_blender_mtx(bone.at_rest_bone_to_model_mtx)
            # Transform light location by bone rest matrix
            light_pos = bone_to_model_mtx @ mathutils.Vector(light.location)
            light.location = light_pos[:3]
            # Transform light rotation by bone rest matrix
            bone_rot_mtx = bone_to_model_mtx.to_3x3()
            light_rot_mtx = light.rotation_quaternion.to_matrix()
            light.rotation_quaternion = (bone_rot_mtx @ light_rot_mtx).to_quaternion()

            light.parent = armature_object
            light.parent_type = 'BONE'
            light.parent_bone = bone.name

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
    
def precompute(ape: Ape):
    data = ModelPrecomputeData(ape)
    data.precompute()
    return data