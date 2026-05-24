from dataclasses import dataclass

from ...types.light import LightFlags, LightType

@dataclass
class ParsedLight:
    name: str
    perpixel_tex_name: str
    corona_tex_name: str
    flags: LightFlags
    light_id: int
    type: LightType
    parent_bone_idx: int
    intensity: float
    motif_color: tuple[float, float, float, float]
    motif_index: int
    radius: float
    pos: tuple[float, float, float]
    mtx_orientation: tuple
    spot_inner_radians: float
    spot_outer_radians: float
    corona_scale: float