from dataclasses import dataclass

@dataclass
class ParsedVolume:
    volume_id: int
    origin: tuple[float, float, float]
    cell_count: int
    cell_first_idx: int
    world_geo_index: int = -1  # index into the world's meshes, -1 for none