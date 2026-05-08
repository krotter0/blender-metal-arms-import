from pathlib import Path

from ....formats.ape.reader import Ape
from ....formats.common.reader import BinaryReader
from ....formats.ape.builders import model_builder
from . import light_builder, worldshape_builder, cell_builder, portal_builder
from ..reader import World, WorldShapeType
from ....common.platform import Platform

class WorldBuildOptions:
    def __init__(self):
        self.platform: Platform = Platform.DX
        self.import_lights = True
        self.import_worldshapes = True
        self.import_cells = True
        self.import_portals = True
        self.import_autoportals = True
        self.load_external_meshes = True
        self.filepath = ""

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
    meshes = {}
    if options.load_external_meshes:
        meshes = _load_external_meshes(world, options)

    for mesh in world.meshes:
        model_builder.build(mesh)

    for i, worldshape in enumerate(world.worldshapes):
        worldshape_builder.build(i, worldshape, meshes)

    for i, light in enumerate(world.vis_data.lights):
        light_builder.build(i, light)

    light_builder.build_ambient(world.vis_data)

    for i, cell in enumerate(world.vis_data.cells):
        cell_builder.build(i, cell)

    for i, portal in enumerate(world.vis_data.portals):
        portal_builder.build(portal)

    for i, volume in enumerate(world.vis_data.volumes):
        print(f"Volume {i}: {volume}")