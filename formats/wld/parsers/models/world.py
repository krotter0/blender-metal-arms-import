from dataclasses import dataclass

from .cells import ParsedCell
from .portals import ParsedVisPortal
from .worldshapes import ParsedWorldShapeInit
from .volumes import ParsedVolume
from ....ape.parsers.models.model import ParsedModel
from ....common.parsers.models.light import ParsedLight

@dataclass
class ParsedVisData:
    ambient_light_color: tuple[float, float, float]
    ambient_light_intensity: float
    portals: list[ParsedVisPortal]
    volumes: list[ParsedVolume]
    cells: list[ParsedCell]
    lights: list[ParsedLight]

    def __post_init__(self):
        if self.lights is None:
            self.lights = []
        if self.portals is None:
            self.portals = []
        if self.volumes is None:
            self.volumes = []
        if self.cells is None:
            self.cells = []

@dataclass
class ParsedWorld:
    meshes: list[ParsedModel]
    vis_data: ParsedVisData
    worldshapes: list[ParsedWorldShapeInit]