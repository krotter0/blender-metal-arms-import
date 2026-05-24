from pathlib import Path
from io import BytesIO
from dataclasses import dataclass

from ...common.builders import light_builder
from ...ape.types.model import FMesh_t
from ...ape.builders import model_builder, material_builder
from ...ape.parsers.model_gc import ModelParserGC
from ...ape.parsers.model_dx import ModelParserDX
from ...ape.parsers.models.model import ParsedModel
from . import worldshape_builder, cell_builder, portal_builder, volume_builder
from ..types.world import PortalFlags, WorldShapeType
from ..parsers.world import ParsedWorld
from ....common.platform import Platform

@dataclass
class WorldBuildOptions:
    platform: Platform = Platform.DX
    import_meshes: bool = True
    import_lights: bool = True
    import_worldshapes: bool = True
    import_cells: bool = True
    import_portals: bool = True
    import_autoportals: bool = True
    load_external_meshes: bool = True
    skip_first_cell: bool = True
    filepath: str = ""
    texture_folder_path: str = None
    texture_allow_recurse: bool = True
    texture_extension: str = ".png"

def _load_external_meshes(world: ParsedWorld, options: WorldBuildOptions) -> dict[str, ParsedModel]:
    used_meshes = set()
    for worldshape in world.worldshapes:
        if worldshape.type == WorldShapeType.MESH and worldshape.shape is not None:
            used_meshes.add(worldshape.shape.mesh_name)

    model_parser = ModelParserDX() if options.platform == Platform.DX else ModelParserGC()

    wld_path = Path(options.filepath)
    loaded_meshes = {}
    for mesh_name in used_meshes:
        ape_path = wld_path.with_name(mesh_name).with_suffix(".ape")
        if ape_path.exists():
            print(f"Loading mesh from {ape_path}")
            ape = FMesh_t()
            ape.bind_to_file(ape_path, big_endian=options.platform.is_big_endian(), tags=[options.platform])
            parsed_model = model_parser.parse(ape, lod_filter={0})
            loaded_meshes[mesh_name] = parsed_model

    return loaded_meshes

def build(world: ParsedWorld, options: WorldBuildOptions = WorldBuildOptions()):
    external_meshes: dict[str, ParsedModel] = {}
    if options.load_external_meshes:
        external_meshes = _load_external_meshes(world, options)
    
    if options.texture_folder_path is not None:
        materials = []
        for mesh in world.meshes:
            materials.extend(mesh.materials)
        for external_mesh in external_meshes.values():
            materials.extend(external_mesh.materials)
        material_builder.build_textures_from_file_system(materials, options.texture_folder_path, options.texture_allow_recurse, [options.texture_extension])

    if options.import_meshes:
        for mesh in world.meshes:
            model_options = model_builder.ModelBuildOptions()
            model_options.platform = options.platform
            model_options.create_armature = False
            model_options.merge_clusters = False
            model_options.apply_lod_name_prefix = False
            model_builder.build(mesh, model_options)

    if options.import_worldshapes:
        for i, worldshape in enumerate(world.worldshapes):
            worldshape_builder.build(i, worldshape, external_meshes)

    if options.import_lights:
        for i, light in enumerate(world.vis_data.lights):
            light_builder.build(i, light)

        light_builder.build_ambient(world.vis_data.ambient_light_color, world.vis_data.ambient_light_intensity)

    if options.import_cells:
        first_volume = 1 if options.skip_first_cell else 0
        for volume in world.vis_data.volumes[first_volume:]:
            volume_builder.build(volume, world.vis_data.cells)

    if options.import_portals:
        for portal in world.vis_data.portals:
            if options.import_autoportals or not (portal.flags & PortalFlags.AUTO_PORTAL):
                portal_builder.build(portal)