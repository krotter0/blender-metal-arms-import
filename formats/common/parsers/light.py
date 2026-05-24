from ..types.light import FLightInit_t
from .models.light import ParsedLight

class LightParser:
    def parse(self, light: FLightInit_t):
        mtx = light.mtx_orientation
        mtx = (
            (mtx[0][0], mtx[2][0], mtx[1][0], mtx[3][0]),
            (mtx[0][2], mtx[2][2], mtx[1][2], mtx[3][2]),
            (mtx[0][1], mtx[2][1], mtx[1][1], mtx[3][1]),
            (0.0, 0.0, 0.0, 1.0),
        )
        pos = (light.influence.pos[0], light.influence.pos[2], light.influence.pos[1])
        return ParsedLight(
            name=light.name,
            perpixel_tex_name=light.perpixel_tex_name,
            corona_tex_name=light.corona_tex_name,
            flags=light.flags,
            light_id=light.light_id,
            type=light.type,
            parent_bone_idx=light.parent_bone_idx,
            intensity=light.intensity,
            motif_color=(light.motif.r, light.motif.g, light.motif.b, light.motif.a),
            motif_index=light.motif.motif_index,
            radius=light.influence.radius,
            pos=pos,
            mtx_orientation=mtx,
            spot_inner_radians=light.spot_inner_radians,
            spot_outer_radians=light.spot_outer_radians,
            corona_scale=light.corona_scale
        )