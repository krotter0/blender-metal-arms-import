from .cells import CellParser
from .models.volumes import ParsedVolume
from ..types.world import FVisVolume_t

class VolumeParser:
    def __init__(self):
        self._cell_parser = CellParser()

    def parse(self, volume: FVisVolume_t) -> ParsedVolume:
        return ParsedVolume(
            volume_id=volume.volume_id,
            origin=volume.bounding_sphere_ws.pos,
            cell_count=volume.cell_count,
            cell_first_idx=volume.cell_first_idx,
            world_geo_index=-1 if volume.world_geo_index == 0xFFFFFFFF else volume.world_geo_index,
        )