from .model import ModelParser
from .models.model import ParsedMesh
from .skeleton_dx import SkeletonParserDX
from .material import MaterialParser

from ....structs.pointer import Pointer

from ..types.model_dx import *
from ..types.model import *
from .. import dx_vbinfo

class _ParsedVBDX:
    def __init__(self):
        self.verts = None
        self.uvs = None
        self.normals = None
        self.colors = None
        self.color_channels = 0
        self.uv_channels = 0

class ModelParserDX(ModelParser):
    def __init__(self):
        super().__init__(SkeletonParserDX(), MaterialParser(Platform.DX))
        self._ibs: list[list[int]] = []
        self._vbs: list[_ParsedVBDX] = []
        self._mesh_is: FDX8Mesh_t = None

    def _parse_vertex_buffer(self, vb: FDX8VB_t):
        vertex_info = dx_vbinfo.get_vb_info(vb.info_index)
        vertex_type = dx_vbinfo.get_vb_vertex_type(vb.info_index)
        vtx_buffer_ptr: Pointer[dx_vbinfo.DXVertexFormat] = vb.dxvb.cast(vertex_type).iterable(vb.vtx_count)
        
        verts = []
        uvs = []
        normals = []
        colors = []

        uv_count = vertex_info.tc_count
        normal_count = vertex_info.normal_count
        color_count = vertex_info.color_count

        for vertex in vtx_buffer_ptr:
            vertex_pos = vertex.pos
            vertex_uvs = vertex.uvs
            vertex_normals = vertex.normals
            vertex_colors = vertex.colors
            verts.append((vertex_pos[0], vertex_pos[2], vertex_pos[1]))
            uvs.append([(vertex_uvs[i].x, -vertex_uvs[i][1]) for i in range(uv_count)])
            normals.append([(vertex_normals[i].x, vertex_normals[i].z, vertex_normals[i].y) for i in range(normal_count)])
            colors.append([(vertex_colors[i].b / 255.0, vertex_colors[i].g / 255.0, vertex_colors[i].r / 255.0, vertex_colors[i].a / 255.0) for i in range(color_count)])
        
        parsed_vb = _ParsedVBDX()
        parsed_vb.verts = verts
        parsed_vb.uvs = uvs
        parsed_vb.normals = normals
        parsed_vb.colors = colors
        parsed_vb.color_channels = color_count
        parsed_vb.uv_channels = uv_count
        return parsed_vb
    
    def _parse_index_buffers(self):
        dxibs = self._mesh_is.dxibs
        ibs = []
        for i in range(self._mesh_is.ib_count):
            ib = []
            num_indices = self._mesh_is.indices_count[i]
            ib_iterable = dxibs[i].iterable(num_indices)
            for j in range(num_indices):
                ib.append(ib_iterable[j])
            ibs.append(ib)
        return ibs
    
    def _parse_vertex_buffers(self):
        vertex_buffers = []
        for i in range(self._mesh_is.vb_count):
            vb = self._mesh_is.vb[i]
            parsed_vb = self._parse_vertex_buffer(vb)
            vertex_buffers.append(parsed_vb)
        return vertex_buffers

    def _get_cluster_buffers(self, vb: _ParsedVBDX, ib: list[int], faces: list[tuple[int, int, int]]):
        vertices_count = 0
        vertex_remap = {}
        
        used_indices = set()
        used_indices.update(*faces)

        for index in used_indices:
            vertex_remap[index] = vertices_count
            vertices_count += 1
        
        verts = [vb.verts[i] for i in used_indices]
        uvs = [vb.uvs[i] for i in used_indices]
        normals = [vb.normals[i] for i in used_indices]
        colors = [vb.colors[i] for i in used_indices]
        faces = [(vertex_remap[i0], vertex_remap[i1], vertex_remap[i2]) for (i0, i1, i2) in faces]
        return verts, uvs, normals, colors, faces

    def _parse_cluster(self, cluster: FDX8MeshCluster_t, material_idx: int):
        ib_index = cluster.ib_index
        ib = self._ibs[ib_index]
        tri_list = cluster.tri_list

        faces = []
        if tri_list.tri_count > 0:
            tri_list_faces = self._indices_to_triangle_list_faces(ib, tri_list.tri_count, tri_list.start_vindex)
            faces.extend(tri_list_faces)

        if cluster.strip_count > 0:
            for strip_buffer in cluster.strip_buffers:
                strip_faces = self._indices_to_triangle_strip_faces(ib, strip_buffer.tri_count, strip_buffer.start_vindex)
                faces.extend(strip_faces)

        seg = self._model.segs[cluster.segment_idx]
        bone_idx = seg.bone_mtx_indices[0] if seg.bone_mtx_count > 0 else None

        vb = self._vbs[cluster.vb_index]
        verts, uvs, normals, colors, faces = self._get_cluster_buffers(vb, ib, faces)
        bone_indices = [bone_idx] * len(verts)
        material_indices = [material_idx] * len(faces)

        return ParsedMesh(
            verts=verts,
            uvs=uvs,
            normals=normals,
            colors=colors,
            faces=faces,
            color_channels=vb.color_channels,
            uv_channels=vb.uv_channels,
            bone_indices=bone_indices,
            material_indices=material_indices,
            lod_id=cluster.lod_id
        )
    
    def _parse_clusters(self):
        for mat_idx, mat in enumerate(self._model.materials):
            for cluster in mat.platform_data_dx.deref.clusters:
                if self._lod_filter is not None and cluster.lod_id not in self._lod_filter:
                    continue
                
                mesh = self._parse_cluster(cluster, mat_idx)
                self._parsed_model.meshes.append(mesh)

    def _parse_platform_specific(self):
        self._mesh_is = self._model.mesh_is_dx.deref

        self._ibs = self._parse_index_buffers()
        self._vbs = self._parse_vertex_buffers()

        if self._model.materials is not None:
            self._parse_clusters()

        self._mesh_is = None