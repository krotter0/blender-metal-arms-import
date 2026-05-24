
from dataclasses import dataclass
from typing import Self

from ....common.parsers.models.light import ParsedLight
from .skeleton import ParsedSkeleton
from .material import ParsedMaterial

@dataclass
class ParsedMesh:
    faces: list[tuple[int, int, int]]
    verts: list[tuple[float, float, float]]
    uvs: list[list[tuple[float, float]]]
    normals: list[list[tuple[float, float, float]]]
    colors: list[list[tuple[float, float, float, float]]]
    bone_indices: list[int]
    material_indices: list[int]
    color_channels: int
    uv_channels: int
    lod_id: int

    @staticmethod
    def merge_meshes(meshes: list[Self]):
        faces = []
        verts = []
        uvs = []
        normals = []
        colors = []
        bone_indices = []
        material_indices = []

        faces_offset = 0

        color_channels = 0
        uv_channels = 0

        lod_id = meshes[0].lod_id

        for mesh in meshes:
            verts.extend(mesh.verts)
            uvs.extend(mesh.uvs)
            normals.extend(mesh.normals)
            colors.extend(mesh.colors)
            bone_indices.extend(mesh.bone_indices)
            material_indices.extend(mesh.material_indices)

            color_channels = max(color_channels, mesh.color_channels)
            uv_channels = max(uv_channels, mesh.uv_channels)
            lod_id = min(lod_id, mesh.lod_id)

            faces.extend([(f[0] + faces_offset, f[1] + faces_offset, f[2] + faces_offset) for f in mesh.faces])

            faces_offset += len(mesh.verts)
        
        return ParsedMesh(
            verts=verts,
            faces=faces,
            uvs=uvs,
            normals=normals,
            colors=colors,
            color_channels=color_channels,
            uv_channels=uv_channels,
            bone_indices=bone_indices,
            material_indices=material_indices,
            lod_id=lod_id
        )

@dataclass
class ParsedModel:
    name: str = None
    meshes: list[ParsedMesh] = None
    skeleton: ParsedSkeleton = None
    lights: list[ParsedLight] = None
    materials: list[ParsedMaterial] = None

    def __post_init__(self):
        if self.meshes is None:
            self.meshes = []
        if self.lights is None:
            self.lights = []