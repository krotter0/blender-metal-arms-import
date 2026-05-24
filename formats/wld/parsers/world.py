from ....structs.pointer import Pointer

from ...ape.parsers.model_dx import ModelParserDX
from ...ape.parsers.model_gc import ModelParserGC
from ...ape.parsers.models.model import ParsedModel

from ....common.platform import Platform
from ...ape.types.model import FMesh_t
from ..types.world import (
    CFWorldShapeInit,
    FData_WorldFileHeader_t,
    FVisData_t,
)
from .cells import CellParser
from .portals import PortalParser
from .worldshapes import WorldShapeParser
from .volumes import VolumeParser
from .models.world import ParsedWorld, ParsedVisData
from ...common.parsers.light import LightParser

class WorldParser:
    def __init__(self, platform: Platform):
        self._platform = platform
        self._portal_parser = PortalParser()
        self._cell_parser = CellParser()
        self._worldshape_parser = WorldShapeParser()
        self._volume_parser = VolumeParser()
        self._light_parser = LightParser()
        self._model_parser = ModelParserDX() if platform == Platform.DX else ModelParserGC()

    def _parse_meshes(self, world: FData_WorldFileHeader_t):
        meshes: list[ParsedModel] = []
        
        if world.num_meshes == 0:
            return meshes
        
        mesh_memory = world.memory.copy()
        mesh = FMesh_t()
        mesh.bind(mesh_memory)

        for init_address in world.mesh_inits:
            mesh_memory.set_offset(init_address)
            parsed_mesh = self._model_parser.parse(mesh, lod_filter={0}, streaming_pointer=world.streaming_data_offset)
            meshes.append(parsed_mesh)

        return meshes

    def _parse_vis_data(self, world: FData_WorldFileHeader_t):
        memory = world.memory.copy(world.world_offset)
        vis_ptr = Pointer[FVisData_t](memory, 0, FVisData_t)

        vis_data = vis_ptr.deref
        portals = [self._portal_parser.parse(portal) for portal in vis_data.portals]
        volumes = [self._volume_parser.parse(volume) for volume in vis_data.volumes]
        cells = [self._cell_parser.parse(cell) for cell in vis_data.cells]
        lights = [self._light_parser.parse(light) for light in vis_data.lights]

        return ParsedVisData(
            ambient_light_color=(vis_data.ambient_light_color[0], vis_data.ambient_light_color[1], vis_data.ambient_light_color[2]),
            ambient_light_intensity=vis_data.ambient_light_intensity,
            portals=portals,
            volumes=volumes,
            cells=cells,
            lights=lights,
        )
    
    def _parse_worldshapes(self, world: FData_WorldFileHeader_t):
        init_header_ptr = world.init_header
        init_header = init_header_ptr.deref

        worldshape_count = init_header.num_init_structs
        worldshapes_address = (init_header_ptr + 1).address

        memory = world.memory.copy(worldshapes_address)
        worldshapes_ptr = Pointer(memory, 0, CFWorldShapeInit).iterable(worldshape_count)

        worldshapes = []

        for worldshape_init in worldshapes_ptr:
            parsed_worldshape = self._worldshape_parser.parse(worldshape_init)
            worldshapes.append(parsed_worldshape)

        return worldshapes

    def parse(self, world: FData_WorldFileHeader_t):
        return ParsedWorld(
            meshes=self._parse_meshes(world),
            vis_data=self._parse_vis_data(world),
            worldshapes=self._parse_worldshapes(world)
        )
