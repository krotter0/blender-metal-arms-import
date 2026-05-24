from dataclasses import dataclass

from ...types.world import PortalFlags

@dataclass
class ParsedVisPortal:
    flags: PortalFlags
    portal_id: int
    origin: tuple[float, float, float]
    vertices: list[tuple[float, float, float]]
    normal: tuple[float, float, float]