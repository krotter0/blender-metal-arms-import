# Blender Metal Arms Import
Blender importer addon for compiled Metal Arms: Glitch in the System assets 

## Lightmap recovery

A compiled world keeps its baked lightmaps but not most of what pasm's lightmapper read to bake them. `LightMapData/Recovered/<world>.txt` holds that lost data for each of the game's 58 worlds (the format is in `LightMapData/FORMAT.md`). When a `.wld` is imported with **Restore Lightmap Data** on (the default), the importer looks for the file whose name matches the world's file name, first in the optional **Lightmap Data Folder**, then in the add-on's own `LightMapData/Recovered`, and puts the data back:

| Recovered | In Blender |
|---|---|
| Lightmap-only lights (and the floor ambient) | Lights named `<name>*onlylm` in a `<world>_lightmap_lights` collection; exact values (game axes, the spot direction's length, APE flags) in the `ma_lightmap` property |
| Fixes to lights the world kept | `*lm` on the ambient / light name, the source's direction vector in `ma_lightmap` |
| Materials that don't block light; vertex radiosity / unlit materials | `*nolmblock`, `*vertrad`, `*notinlm` on the material name (and in its `ma_lightmap` property, since names stop at 63 characters) |
| Placed objects left out of the bake | `*nolmuse` on the `obj_<mesh>` name |
| Source triangle order | Faces sorted by it, and the global rank in the `ma_lm_order` face attribute |
| Art colours of vertex radiosity vertices | `color_0` (pasm's baked colours kept in `color_0_baked`) |
| Bake settings | A `<world>.aid` text block |

A `<world>_lightmap_recovery.txt` text block reports what was applied. Each file names the SHA-256 of the retail Xbox world it was made for: when the imported file matches, everything is applied; when it doesn't (another platform or build), only data that can be checked by name or position is (lights, `.aid`, materials and objects whose texture / mesh names match), and the triangle order and vertex colours are left out. `#! apetris` hand edits (two worlds) are not replayed.
