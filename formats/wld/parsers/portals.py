from ..types.world import FVisPortal_t
from .models.portals import ParsedVisPortal


class PortalParser:
    def parse(self, portal: FVisPortal_t):
        vertices = [portal.vertices[i] for i in range(min(4, portal.vert_count))]
        return ParsedVisPortal(
            flags=portal.flags,
            portal_id=portal.portal_id,
            vertices=[(vertex[0], vertex[2], vertex[1]) for vertex in vertices],
            normal=(portal.normal[0], portal.normal[2], portal.normal[1]),
            origin=(portal.bounding_sphere_ws.pos[0], portal.bounding_sphere_ws.pos[2], portal.bounding_sphere_ws.pos[1]),
        )
