"""Builds what lightmap recovery puts back into the Blender scene (see formats/wld/lightmap_recovery.py).

- the lightmap-only lights, in a collection of their own, named with their star commands (`*onlylm`, ...);
- on each world mesh object: the source triangle order as the face attribute `ma_lm_order`, and the art's colours on
  the vertex radiosity vertices in `color_0` (pasm's baked colours kept in `color_0_baked`);
- the star commands added to materials, also as the custom property `ma_lightmap` (names can be cut at 63 characters);
- the `.aid` settings and a report as text blocks.
"""

import bpy
from mathutils import Vector

from ...common.builders import light_builder
from .. import lightmap_recovery as lr

ORDER_ATTRIBUTE = "ma_lm_order"
COLOR_ATTRIBUTE = "color_0"
BAKED_COLOR_ATTRIBUTE = "color_0_baked"

_BLENDER_LIGHT_TYPES = {
    lr.APE_LIGHT_SPOT: 'SPOT',
    lr.APE_LIGHT_OMNI: 'POINT',
    lr.APE_LIGHT_DIR: 'SUN',
}

_MIN_SPOT_SIZE = 0.0174533     # Blender's spot_size range: 1 to 180 degrees
_MAX_SPOT_SIZE = 3.14159265


def _light_props(light: lr.RecoveredLight) -> dict:
    props = {
        "recovered": True,
        "ape_type": light.type,
        "ape_flags": light.flags,
        "position": list(light.pos),        # game axes (Y up), as the source wrote them
        "direction": list(light.dir),       # length kept: pasm's spot cone uses the vector as written
        "radius": light.radius,
        "color": list(light.color),
        "intensity": light.intensity,
        "source": light.line,
    }
    if light.type == lr.APE_LIGHT_SPOT:
        props["spot_inner"] = light.spot_inner
        props["spot_outer"] = light.spot_outer
    if light.light_id is not None:
        props["light_id"] = light.light_id
    if light.motif is not None:
        props["motif"] = light.motif
    return props


def _build_recovered_light(index: int, light: lr.RecoveredLight, collection: bpy.types.Collection):
    name = light.base_name or f"lmlight_{index}"
    props = _light_props(light)

    if light.type == lr.APE_LIGHT_AMBIENT:
        # (pasm's exporter makes an ambient light of a helper whose name starts "ambient")
        if not name.lower().startswith("ambient"):
            name = "ambient_" + name
        return light_builder.build_ambient(light.color, light.intensity, name, light.star_commands, props, collection)

    blender_type = _BLENDER_LIGHT_TYPES.get(light.type)
    if blender_type is None:
        print(f"Lightmap recovery: unsupported light type {light.type}: {light.line}")
        return None

    data = bpy.data.lights.new(name, type=blender_type)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)

    if light.type != lr.APE_LIGHT_DIR:
        obj.location = lr.to_blender_vec(light.pos)
    direction = Vector(lr.to_blender_vec(light.dir))
    if light.type in (lr.APE_LIGHT_SPOT, lr.APE_LIGHT_DIR) and direction.length > 1e-9:
        # Blender lights shine down their local -Z
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = direction.normalized().to_track_quat('-Z', 'Y')

    if light.type == lr.APE_LIGHT_SPOT:
        data.spot_size = min(max(light.spot_outer, _MIN_SPOT_SIZE), _MAX_SPOT_SIZE)
        if light.spot_outer > 0:
            data.spot_blend = min(max(1.0 - light.spot_inner / light.spot_outer, 0.0), 1.0)

    light_builder.set_light_values(obj, light.color, light.intensity, light.radius)
    light_builder.apply_star_commands_and_props(obj, light.star_commands, props)
    return obj


def build_lights(result: lr.RecoveryResult, world_name: str, parent_collection: bpy.types.Collection = None):
    """The lightmap-only lights, in a collection of their own under the given one."""
    if not result.lights:
        return None
    parent_collection = parent_collection or bpy.context.collection
    collection = bpy.data.collections.new(f"{world_name}_lightmap_lights")
    parent_collection.children.link(collection)
    for i, light in enumerate(result.lights):
        _build_recovered_light(i, light, collection)
    return collection


def _set_face_order(mesh: bpy.types.Mesh, ranks: list[int]):
    if len(ranks) != len(mesh.polygons):
        print(f"Lightmap recovery: {mesh.name} has {len(mesh.polygons)} faces, the order {len(ranks)}: not set")
        return
    attribute = mesh.attributes.get(ORDER_ATTRIBUTE)
    if attribute is None:
        attribute = mesh.attributes.new(ORDER_ATTRIBUTE, 'INT', 'FACE')
    attribute.data.foreach_set("value", ranks)


def _set_art_colors(mesh: bpy.types.Mesh, colors: dict[int, tuple[int, int, int]]):
    count = len(mesh.vertices)
    attribute = mesh.color_attributes.get(COLOR_ATTRIBUTE)
    if attribute is not None and (attribute.domain != 'POINT' or len(attribute.data) != count):
        print(f"Lightmap recovery: {mesh.name}'s {COLOR_ATTRIBUTE} is not per vertex: art colours not set")
        return

    values = [1.0] * (count * 4)
    if attribute is None:
        mesh.color_attributes.new(COLOR_ATTRIBUTE, 'BYTE_COLOR', 'POINT')
    else:
        attribute.data.foreach_get("color", values)
        if mesh.color_attributes.get(BAKED_COLOR_ATTRIBUTE) is None:
            baked = mesh.color_attributes.new(BAKED_COLOR_ATTRIBUTE, 'BYTE_COLOR', 'POINT')
            baked.data.foreach_set("color", values)

    # (the same scale the importer reads vertex colours with: byte / 255)
    for local, (r, g, b) in colors.items():
        if 0 <= local < count:
            values[local * 4] = r / 255.0
            values[local * 4 + 1] = g / 255.0
            values[local * 4 + 2] = b / 255.0

    # (adding an attribute can invalidate earlier references to the mesh's attributes: look it up again)
    attribute = mesh.color_attributes.get(COLOR_ATTRIBUTE)
    attribute.data.foreach_set("color", values)
    try:
        mesh.color_attributes.active_color = attribute
        mesh.color_attributes.render_color_index = mesh.color_attributes.find(COLOR_ATTRIBUTE)
    except (AttributeError, TypeError):
        pass


def _tag_materials(result: lr.RecoveryResult, mesh_index: int, mesh: bpy.types.Mesh):
    for material_index, commands in result.material_star_commands.items():
        if material_index[0] != mesh_index or material_index[1] >= len(mesh.materials):
            continue
        material = mesh.materials[material_index[1]]
        if material is None or "ma_lightmap" in material:
            continue
        material["ma_lightmap"] = {"star_commands": "*" + "*".join(commands)}
        missing = [c for c in commands if ("*" + c) not in material.name]
        if missing:
            print(f"Lightmap recovery: material name '{material.name}' is too long for {missing}; they are in its ma_lightmap property")


def apply_to_mesh_objects(result: lr.RecoveryResult, mesh_index: int, objects: list[bpy.types.Object]):
    """Face order, art colours and material tags on a world mesh's objects (one per parsed mesh, in order)."""
    for p, obj in enumerate(objects or []):
        if obj is None or obj.type != 'MESH':
            continue
        mesh: bpy.types.Mesh = obj.data
        ranks = result.face_order.get((mesh_index, p))
        if ranks is not None:
            _set_face_order(mesh, ranks)
        colors = result.art_colors.get((mesh_index, p))
        if colors:
            _set_art_colors(mesh, colors)
        _tag_materials(result, mesh_index, mesh)


def build_texts(result: lr.RecoveryResult, world_name: str):
    """The .aid settings and the report, as text blocks."""
    data = result.data
    if result.aid_lines:
        aid = bpy.data.texts.new(f"{world_name}.aid")
        aid.write("\n".join(result.aid_lines) + "\n")

    lines = [
        f"Lightmap recovery for {world_name}",
        f"file: {data.path}",
        f"sha256: {'matches this world' if result.exact else 'does NOT match this world (only name-checked data applied)'}",
        "",
    ]
    lines.extend(result.report)
    if result.warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"  {w}" for w in result.warnings)
    if data.apetris:
        lines.append("")
        lines.append("not applied (#! apetris):")
        lines.extend(f"  {a}" for a in data.apetris)
    lines.append("")
    lines.append("Blender data: lights in the '_lightmap_lights' collection (custom property ma_lightmap); world mesh")
    lines.append(f"faces' source order in the '{ORDER_ATTRIBUTE}' face attribute; art colours in '{COLOR_ATTRIBUTE}' (baked ones")
    lines.append(f"in '{BAKED_COLOR_ATTRIBUTE}'); added material / object star commands also in their ma_lightmap property.")
    report = bpy.data.texts.new(f"{world_name}_lightmap_recovery.txt")
    report.write("\n".join(lines) + "\n")


def build(result: lr.RecoveryResult, world_name: str, import_lights: bool = True):
    if import_lights:
        build_lights(result, world_name)
    build_texts(result, world_name)
