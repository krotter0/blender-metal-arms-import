from .model import ModelParser
from .models.model import ParsedMesh
from .skeleton_gc import SkeletonParserGC
from .material import MaterialParser

from ....structs.stream import Stream

from ..types.model_gc import *
from ..types.model import *
from .model_normalsphere import NORMAL_SPHERE

_POS_FRAC_ADJUSTS = [(1.0 / (1 << i)) for i in range(16)]
_UV_FRAC_ADJUST = 1 / (1 << 8)

class _ParsedVBGC:
    def __init__(self):
        self.verts: list[tuple[float, float, float]] = []
        self.normals: list[tuple[float, float, float]] | None = None
        self.uvs: list[tuple[float, float]] = []
        self.colors: list[tuple[float, float, float, float]] | None = None
        self.flags: GCVBFlags = GCVBFlags.NONE
        self.pos_idx_format: FieldType = None
        self.color_idx_format: FieldType = None

class GXPrimitiveType(Flag):
    TRIANGLESTRIP = 0x98
    TRIANGLES = 0x90

class _GCDisplayListPrimitive:
    def __init__(self, primitive_type: GXPrimitiveType, indices_count: int, pos_indices: list[int], normal_indices: list[int] | None, binormal_indices: list[int] | None, tangent_indices: list[int], diffuse_indices: list[int] | None, st_indices: list[list[int]]):
        self.primitive_type = primitive_type
        self.num_indices = indices_count
        self.pos_indices = pos_indices
        self.normal_indices = normal_indices
        self.binormal_indices = binormal_indices
        self.tangent_indices = tangent_indices
        self.diffuse_indices = diffuse_indices
        self.st_indices = st_indices

class ModelParserGC(ModelParser):
    def __init__(self):
        super().__init__(SkeletonParserGC(), MaterialParser(Platform.GC))
        self._vbs: list[_ParsedVBGC] = []
        self._material_dl_buffers: list[list[list[_GCDisplayListPrimitive]]] = []
        self._sts_sizes: list[int] = []
        self._nbt_sizes: list[int] = []
        self._mesh_is: FGCMesh_t = None

    def _parse_displaylist_buffer(self, dl_container: FGC_DLCont_t, st_sets: int, vb_has_nbt: bool, vb_pos_idx_format: FieldType, vb_color_idx_format: FieldType) -> list[_GCDisplayListPrimitive]:
        primitives: list[_GCDisplayListPrimitive] = []
        pointer = dl_container.buffer
        container_flags = dl_container.flags
        if container_flags & GCDLContFlags.STREAMING:
            if self._streaming_pointer is None:
                raise ValueError("Display list is marked as streaming but no streaming pointer was provided to the model parser.")
            streaming_offset = pointer.address
            pointer = self._streaming_pointer + streaming_offset
        
        stream = Stream.from_pointer(pointer)
        primitive_count = dl_container.strip_count + dl_container.list_count

        has_nbt = vb_has_nbt and container_flags & GCDLContFlags.STREAMING
        has_color = not container_flags & GCDLContFlags.CONSTANT_COLOR

        while primitive_count > 0:
            primitive_count -= 1
            opcode = stream.read(u8)

            vtx_fmt = GCVertexFormat(opcode & 0x7)
            primitive_type = GXPrimitiveType(opcode & 0xF8)
            assert primitive_type in (GXPrimitiveType.TRIANGLESTRIP, GXPrimitiveType.TRIANGLES), f"GX DisplayList Opcode is neither of the expected primitive types: {opcode}"

            num_indices = stream.read(u16)

            pos_indices = []
            normal_indices = []
            binormal_indices = [] if has_nbt else None
            tangent_indices = [] if has_nbt else None
            diffuse_indices = [] if has_color else None
            st_indices = [[] for _ in range(st_sets)]
            for _ in range(num_indices):
                pos_idx = stream.read(vb_pos_idx_format)
                pos_indices.append(pos_idx)

                norm_idx = stream.read(u16)
                normal_indices.append(norm_idx)

                binormal_idx, tangent_idx, diffuse_idx = None, None, None
                if has_nbt:
                    binormal_idx = stream.read(u16)
                    binormal_indices.append(binormal_idx)
                    tangent_idx = stream.read(u16)
                    tangent_indices.append(tangent_idx)

                if has_color:
                    diffuse_idx = stream.read(vb_color_idx_format)
                    diffuse_indices.append(diffuse_idx)

                for j in range(st_sets):
                    st_idx = stream.read(u16)
                    st_indices[j].append(st_idx)

            primitive = _GCDisplayListPrimitive(primitive_type, num_indices, pos_indices, normal_indices, binormal_indices, tangent_indices, diffuse_indices, st_indices)
            primitives.append(primitive)

        return primitives
        

    def _parse_mesh(self, dl_container: FGC_DLCont_t, mat_idx: int, dl_idx: int, st_sets: int):
        mat_dl_buffers = self._material_dl_buffers[mat_idx]
        if dl_idx >= len(mat_dl_buffers):
            return None
        dl_primitives = mat_dl_buffers[dl_idx]
        
        
        vertices_count = 0
        vertex_remap = {}
        
        vb = self._vbs[dl_container.vb_index]

        constant_color = dl_container.constant_color
        constant_color = (constant_color.r / 255, constant_color.g / 255, constant_color.b / 255, constant_color.a / 255)

        uses_sphere_normal = vb.normals == None
        constant_color = dl_container.flags & GCDLContFlags.CONSTANT_COLOR
        bone_idx = dl_container.matrix_idx

        verts = []
        uvs = []
        faces = []
        normals = []
        colors = None if constant_color else []

        for primitive in dl_primitives:
            primitive_vertex_indices = []

            for i in range(primitive.num_indices):
                vertex_index = vertices_count

                pos_index = primitive.pos_indices[i]
                normal_index = primitive.normal_indices[i]
                st_indices = [primitive.st_indices[j][i] for j in range(st_sets)]
                binormal_index = primitive.binormal_indices[i] if primitive.binormal_indices is not None else None
                tangent_index = primitive.tangent_indices[i] if primitive.tangent_indices is not None else None
                diffuse_index = primitive.diffuse_indices[i] if primitive.diffuse_indices is not None else None

                vertex_key = (pos_index,
                          normal_index,
                          tuple(st_indices),
                          binormal_index,
                          tangent_index,
                          diffuse_index)
                if vertex_key in vertex_remap:
                    vertex_index = vertex_remap[vertex_key]
                else:
                    vertex_remap[vertex_key] = vertex_index
                    vertices_count += 1

                    vert_pos = vb.verts[pos_index]
                    vert_uvs = [vb.uvs[st_idx] for st_idx in st_indices]
                    if uses_sphere_normal:
                        vert_normal = NORMAL_SPHERE[normal_index]
                    else:
                        vert_normal = vb.normals[normal_index]

                    verts.append(vert_pos)
                    uvs.append(vert_uvs)
                    normals.append([(vert_normal[0], vert_normal[2], vert_normal[1])])

                    if constant_color:
                        colors.append([constant_color])
                    else:
                        vert_color = vb.colors[diffuse_index]
                        colors.append([vert_color])
                primitive_vertex_indices.append(vertex_index)
            
            primitive_faces = None
            if primitive.primitive_type == GXPrimitiveType.TRIANGLESTRIP:
                tri_count = primitive.num_indices - 2
                primitive_faces = self._indices_to_triangle_strip_faces(primitive_vertex_indices, tri_count)
            elif primitive.primitive_type == GXPrimitiveType.TRIANGLES:
                tri_count = primitive.num_indices // 3
                primitive_faces = self._indices_to_triangle_list_faces(primitive_vertex_indices, tri_count)
            faces.extend(primitive_faces)

        bone_indices = [bone_idx] * len(verts)
        material_indices = [mat_idx] * len(faces)
        return ParsedMesh(
            verts=verts,
            uvs=uvs,
            normals=normals,
            colors=colors,
            faces=faces,
            color_channels=1,
            bone_indices=bone_indices,
            uv_channels=st_sets,
            material_indices=material_indices,
            lod_id=dl_container.lod_id
        )

    def _parse_vertex_buffer_positions(self, vb: FGCVB_t):
        verts = []
        pos_frac_adjust = _POS_FRAC_ADJUSTS[vb.pos_frac]
        
        positions_format: type[FieldType] = None
        pos_type = vb.pos_type
        if pos_type == GCVertexPositionType.U8:
            positions_format = u8
        elif pos_type == GCVertexPositionType.S8:
            positions_format = s8
        elif pos_type == GCVertexPositionType.U16:
            positions_format = u16
        elif pos_type == GCVertexPositionType.S16:
            positions_format = s16
        elif pos_type == GCVertexPositionType.F32:
            positions_format = f32
        else:
            raise ValueError(f"Invalid GC Vertex Position Type: {pos_type}")
        pos_count = vb.pos_count
        positions_ptr = vb.positions.cast(positions_format).iterable(pos_count * 3)
        position_components = list(positions_ptr)
        for i in range(0, pos_count * 3, 3):
            x = position_components[i] * pos_frac_adjust
            y = position_components[i + 1] * pos_frac_adjust
            z = position_components[i + 2] * pos_frac_adjust
            adjusted_pos = (x, z, y)
            verts.append(adjusted_pos)
        return verts
    
    def _parse_vertex_buffer_normals(self, vb: FGCVB_t, vb_index: int):
        if vb.nbt == None or vb.nbt.address == 0:
            return None
        nbt_count = self._nbt_sizes[vb_index]
        nbt_ptr = vb.nbt.iterable(nbt_count)
        return [(nbt.nx / 64.0, nbt.nz / 64.0, nbt.ny / 64.0) for nbt in nbt_ptr]
    
    def _parse_vertex_buffer_uvs(self, vb: FGCVB_t, vb_index: int):
        sts_count = self._sts_sizes[vb_index]
        sts_ptr = vb.sts.iterable(sts_count)
        return [(st.s * _UV_FRAC_ADJUST, -st.t * _UV_FRAC_ADJUST) for st in sts_ptr]
    
    def _parse_vertex_buffer_colors(self, vb: FGCVB_t):
        return [(color.r / 255, color.g / 255, color.b / 255, color.a / 255) for color in vb.diffuse]
    
    def _parse_vertex_buffer(self, vb: FGCVB_t, vb_index: int):
        parsed_vb = _ParsedVBGC()

        parsed_vb.verts = self._parse_vertex_buffer_positions(vb)
        parsed_vb.uvs = self._parse_vertex_buffer_uvs(vb, vb_index)
        parsed_vb.normals = self._parse_vertex_buffer_normals(vb, vb_index)
        parsed_vb.colors = self._parse_vertex_buffer_colors(vb)

        parsed_vb.flags = vb.flags

        color_idx_type = vb.color_idx_type
        parsed_vb.color_idx_format = u8 if color_idx_type == GCVertexAttributeType.INDEX8 else u16

        pos_idx_type = vb.pos_idx_type
        parsed_vb.pos_idx_format = u8 if pos_idx_type == GCVertexAttributeType.INDEX8 else u16

        return parsed_vb
    
    def _parse_vertex_buffers(self):
        vertex_buffers = []
        for i in range(self._mesh_is.vb_count):
            vb = self._mesh_is.vb[i]
            parsed_vb = self._parse_vertex_buffer(vb, i)
            vertex_buffers.append(parsed_vb)
        return vertex_buffers
    
    def _calculate_st_nbt_length(self):
        vb_count = self._mesh_is.vb_count
        max_st_idxs: list[int] = [-1] * vb_count
        max_nbt_idxs: list[int] = [-1] * vb_count

        for mat_idx, mat in enumerate(self._model.materials):
            dl_containers = mat.platform_data_gc.deref.dl_container
            dl_buffers = self._material_dl_buffers[mat_idx]

            for dl_idx, dl_container in enumerate(dl_containers):
                if dl_idx >= len(dl_buffers):
                    continue

                vb_index = dl_container.vb_index
                primitives = dl_buffers[dl_idx]

                for primitive in primitives:
                    max_normal_idx = max(primitive.normal_indices, default=-1) if primitive.normal_indices is not None else -1
                    max_bitangent_idx = max(primitive.binormal_indices, default=-1) if primitive.binormal_indices is not None else -1
                    max_tangent_idx = max(primitive.tangent_indices, default=-1) if primitive.tangent_indices is not None else -1

                    primitive_max_nbt_idx = max(max_normal_idx, max_bitangent_idx, max_tangent_idx)
                    max_nbt_idxs[vb_index] = max(max_nbt_idxs[vb_index], primitive_max_nbt_idx)

                    for st_set in primitive.st_indices:
                        primitive_max_st_idx = max(st_set, default=-1)
                        max_st_idxs[vb_index] = max(max_st_idxs[vb_index], primitive_max_st_idx)

        st_counts = [max_st_idx + 1 for max_st_idx in max_st_idxs]
        nbt_counts = [max_nbt_idx + 1 for max_nbt_idx in max_nbt_idxs]
        return (st_counts, nbt_counts)
    
    def _parse_dl_buffers(self):
        if self._model.material_count == 0:
            return
        
        vb_has_nbts = []
        vb_pos_formats = []
        vb_color_formats = []
        for vb in self._mesh_is.vb:
            vb_has_nbts.append(vb.flags & GCVBFlags.NORM_NBT)
            vb_pos_formats.append(u8 if vb.pos_idx_type == GCVertexAttributeType.INDEX8 else u16)
            vb_color_formats.append(u8 if vb.color_idx_type == GCVertexAttributeType.INDEX8 else u16)

        for mat in self._model.materials:
            dl_buffers = []
            st_sets = mat.base_st_sets + mat.lightmap_st_sets
            for dl_container in mat.platform_data_gc.deref.dl_container:
                vb_index = dl_container.vb_index
                vb_has_nbt = vb_has_nbts[vb_index]
                pos_format = vb_pos_formats[vb_index]
                color_format = vb_color_formats[vb_index]
                buffer = self._parse_displaylist_buffer(dl_container, st_sets, vb_has_nbt, pos_format, color_format)
                dl_buffers.append(buffer)
            self._material_dl_buffers.append(dl_buffers)

    def _parse_dl_meshes(self):
        if self._model.material_count == 0:
            return
        
        for mat_idx, mat in enumerate(self._model.materials):
            base_st_sets = mat.base_st_sets
            lightmap_st_sets = mat.lightmap_st_sets
            st_sets = base_st_sets + lightmap_st_sets
            for dl_idx, dl_container in enumerate(mat.platform_data_gc.deref.dl_container):
                if self._lod_filter is not None and dl_container.lod_id not in self._lod_filter:
                    continue

                mesh = self._parse_mesh(dl_container, mat_idx, dl_idx, st_sets)
                self._parsed_model.meshes.append(mesh)

    def _parse_platform_specific(self):
        self._mesh_is = self._model.mesh_is_gc.deref

        self._parse_dl_buffers()

        self._sts_sizes, self._nbt_sizes = self._calculate_st_nbt_length()
        self._vbs = self._parse_vertex_buffers()
        
        self._parse_dl_meshes()

        self._mesh_is = None
        self._vbs = []
        self._material_dl_buffers = []
        self._sts_sizes = []
        self._nbt_sizes = []
        