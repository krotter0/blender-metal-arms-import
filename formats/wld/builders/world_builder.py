from pathlib import Path

from ...common.builders import light_builder
from ...ape.types.model import Ape
from ....common.binary_reader import BinaryReader
from ....formats.ape.builders import model_builder, material_builder
from . import worldshape_builder, cell_builder, portal_builder
from ..types.world import PortalFlags, World, WorldShapeType
from ....common.platform import Platform

class WorldBuildOptions:
    def __init__(self):
        self.platform: Platform = Platform.DX
        self.import_meshes = True
        self.import_lights = True
        self.import_worldshapes = True
        self.import_cells = True
        self.import_portals = True
        self.import_autoportals = True
        self.load_external_meshes = True
        self.skip_first_cell = True
        self.filepath = ""
        self.texture_folder_path: str = None
        self.texture_allow_recurse: bool = True

def _load_external_meshes(world: World, options: WorldBuildOptions):
    used_meshes = set()
    for worldshape in world.worldshapes:
        if worldshape.type == WorldShapeType.MESH and worldshape.shape is not None:
            used_meshes.add(worldshape.shape.mesh_name)

    wld_path = Path(options.filepath)
    loaded_meshes = {}
    for mesh_name in used_meshes:
        ape_path = wld_path.with_name(mesh_name).with_suffix(".ape")
        if ape_path.exists():
            print(f"Loading mesh from {ape_path}")
            with BinaryReader(ape_path, False) as reader:
                ape = Ape()
                ape.read(reader)
                loaded_meshes[mesh_name] = ape

    return loaded_meshes

def build(world: World, options: WorldBuildOptions = WorldBuildOptions()):
    precomputed_meshes = {}
    if options.load_external_meshes:
        meshes = _load_external_meshes(world, options)
        for mesh_name, ape in meshes.items():
            precomputed_meshes[mesh_name] = model_builder.precompute(ape)

    if options.texture_folder_path is not None:
        apes = []
        for mesh in world.meshes:
            apes.append(mesh)
        for precomputed_mesh in precomputed_meshes.values():
            apes.append(precomputed_mesh.ape)
        material_builder.build_textures_from_file_system(apes, options.texture_folder_path, options.texture_allow_recurse)

    for mesh in world.meshes:
        model_builder.build(mesh)

    if options.import_worldshapes:
        for i, worldshape in enumerate(world.worldshapes):
            worldshape_builder.build(i, worldshape, precomputed_meshes)

    if options.import_lights:
        for i, light in enumerate(world.vis_data.lights):
            light_builder.build(i, light)

        light_builder.build_ambient(world.vis_data.ambient_light_color, world.vis_data.ambient_light_intensity)

    if options.import_cells:
        cell_builder.build_with_volumes(world.vis_data, options.skip_first_cell)

    if options.import_portals:
        for i, portal in enumerate(world.vis_data.portals):
            if options.import_autoportals or not (portal.flags & PortalFlags.AUTO_PORTAL):
                portal_builder.build(portal)