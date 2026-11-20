"""Lightmap recovery data: what pasm's lightmapper read from a world's source that the compiled world no longer holds.

The files (one per world, `LightMapData/Recovered/<world>.txt`, made by unpasm's `lmdata`; the format is described in
`LightMapData/FORMAT.md`) give back the lightmap-only lights, the materials and placed objects that don't block light,
vertex radiosity overrides and art colours, the source triangle order, bake settings (`.aid` lines) and fixes to the
lights the compiled world kept.

This module has no Blender dependency: it reads a file and works out, against a parsed world, what to put back.
`apply()` changes the parsed world in place (material star commands, kept lights' fixes, face order) and returns what
the builders still need to do (lights to create, object star commands, vertex colours, the .aid lines, a report).
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from ...common.star_command_assembler import StarCommand
from ..ape.types.shaders import SurfaceShaderRegisterType, LightShaderRegisterType
from ..common.types.light import LightType
from .types.world import WorldShapeType

# APE (source) light types, as the files write them...
APE_LIGHT_SPOT = 0
APE_LIGHT_OMNI = 1
APE_LIGHT_DIR = 2
APE_LIGHT_AMBIENT = 3

# ...and the compiled world's types for them
_APE_TO_LIGHT_TYPE = {
    APE_LIGHT_SPOT: LightType.SPOT,
    APE_LIGHT_OMNI: LightType.OMNIDIRECTIONAL,
    APE_LIGHT_DIR: LightType.DIRECTIONAL,
    APE_LIGHT_AMBIENT: LightType.AMBIENT,
}

# APE light flags (pasm's ape_file_def.h) and the star commands that set them
APE_LIGHT_FLAG_SELF = 0x02
APE_LIGHT_FLAG_LIGHTMAP_ONLY = 0x10
APE_LIGHT_FLAG_LIGHTMAP = 0x20
APE_LIGHT_FLAG_UNIQUE_LIGHTMAP = 0x40
APE_LIGHT_FLAG_DYNAMIC_ONLY = 0x400
DEFAULT_LIGHTMAP_LIGHT_FLAGS = APE_LIGHT_FLAG_LIGHTMAP_ONLY | APE_LIGHT_FLAG_LIGHTMAP

# APE material flags (unpasm's Decompile.MAT_*) and their star commands
APE_MAT_DO_NOT_LM = 0x04
APE_MAT_NO_LM_USE = 0x20
APE_MAT_DO_NOT_BLOCK_LM = 0x40
APE_MAT_VERT_RADIOSITY = 0x80

# Placed objects: the mesh instance flag unpasm counts "obj<NNN>" over
MESH_INST_FLAG_STATIC = 0x8

STAR_NOLMBLOCK = "nolmblock"
STAR_NOTINLM = "notinlm"
STAR_VERTRAD = "vertrad"
STAR_NOLMUSE = "nolmuse"
STAR_ONLYLM = "onlylm"
STAR_LM = "lm"
STAR_UNIQUELM = "uniquelm"
STAR_SELF = "self"
STAR_AREA_LIGHT = "light"

# The folder of recovery files shipped with the add-on
BUNDLED_DATA_DIR = Path(__file__).resolve().parents[2] / "LightMapData" / "Recovered"

_POS_TOLERANCE = 0.05
_DIR_TOLERANCE = 0.001
_COLOR_TOLERANCE = 0.002


def light_star_commands(flags: int) -> list[str]:
    """The star commands a light's name needs for its APE flags."""
    commands = []
    if flags & APE_LIGHT_FLAG_LIGHTMAP_ONLY:
        commands.append(STAR_ONLYLM)
    elif flags & APE_LIGHT_FLAG_UNIQUE_LIGHTMAP:
        commands.append(STAR_UNIQUELM)
    elif flags & APE_LIGHT_FLAG_LIGHTMAP:
        commands.append(STAR_LM)
    if flags & APE_LIGHT_FLAG_SELF:
        commands.append(STAR_SELF)
    return commands


def to_blender_vec(v):
    """Game / APE (Y up) to Blender (Z up), as the importer converts everything else."""
    return (v[0], v[2], v[1])


# ---------------------------------------------------------------------------------------------------------------------
# The file
# ---------------------------------------------------------------------------------------------------------------------

@dataclass
class RecoveredLight:
    name: str
    type: int                                   # APE type: 0 spot, 1 omni, 2 sun, 3 ambient
    pos: tuple[float, float, float]             # game / APE coordinates (Y up)
    dir: tuple[float, float, float]             # as the source wrote it, length included (pasm's spot cone uses it so)
    radius: float
    color: tuple[float, float, float]           # 0-1
    intensity: float
    spot_inner: float = 0.0                     # full angles, radians (spots)
    spot_outer: float = 0.0
    flags: int = DEFAULT_LIGHTMAP_LIGHT_FLAGS
    light_id: int | None = None
    motif: int | None = None
    line: str = ""

    @property
    def base_name(self) -> str:
        return self.name.split("*")[0]

    @property
    def star_commands(self) -> list[str]:
        return light_star_commands(self.flags)


@dataclass
class KeptLightFix:
    type: int                                   # APE type
    key: tuple[float, float, float]             # position (omni, spot), direction (sun) or colour (ambient)
    or_flags: int = 0
    clear_flags: int = 0
    dir: tuple[float, float, float] | None = None
    remove: bool = False
    line: str = ""


@dataclass
class MaterialRef:
    volume: int
    material: int
    texture: str
    line: str = ""


@dataclass
class AreaLight:
    volume: int
    material: int
    texture: str
    rgbi: tuple[float, float, float, float]
    line: str = ""


@dataclass
class ObjectRef:
    index: int
    mesh: str
    line: str = ""


@dataclass
class ColorRun:
    segment: str
    first_vertex: int
    colors: list[tuple[int, int, int]]          # expanded, 0-255


@dataclass
class LightmapRecoveryData:
    path: Path
    world: str = ""
    floor: tuple[int, int, int] = (0, 0, 0)
    sky_horizon: tuple[int, int, int] = (0, 0, 0)
    sky_zenith: tuple[int, int, int] = (0, 0, 0)
    sha256: str | None = None
    source: str = ""
    notes: list[str] = field(default_factory=list)
    lights: list[RecoveredLight] = field(default_factory=list)
    light_fixes: list[KeptLightFix] = field(default_factory=list)
    aid: list[tuple[str, str]] = field(default_factory=list)
    clear_materials: list[MaterialRef] = field(default_factory=list)
    clear_objects: list[ObjectRef] = field(default_factory=list)
    vertrad: list[MaterialRef] = field(default_factory=list)
    novertrad: list[MaterialRef] = field(default_factory=list)
    areas: list[AreaLight] = field(default_factory=list)
    arealights: list[str] = field(default_factory=list)
    colors: list[ColorRun] = field(default_factory=list)
    order: list[tuple[int, int, int, int]] = field(default_factory=list)    # expanded (volume, material, cluster, tri)
    apetris: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    text: str = ""


def _unescape_name(name: str) -> str:
    if name == "\\e":
        return ""
    if name.startswith("\\h"):
        name = "#" + name[2:]
    return name.replace("\\s", " ")


def _parse_rgb_slash(text: str) -> tuple[int, int, int]:
    parts = text.split("/")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


_HEADER_RE = re.compile(r"^#\s*(?P<world>[^:]+):\s*floor\s+(?P<floor>\d+/\d+/\d+)(?:;\s*sky\s+h\s+(?P<h>\d+/\d+/\d+)\s+z\s+(?P<z>\d+/\d+/\d+))?")
_MATREF_RE = re.compile(r"^vol(\d+):(\d+)(?:\s+(\S+))?")
_OBJREF_RE = re.compile(r"^obj(\d+)(?:\s+(\S+))?")


def _parse_light(line: str) -> RecoveredLight:
    tokens = line.split()
    name = _unescape_name(tokens[0])
    values = []
    options = {}
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            options[key] = value
        else:
            values.append(float(token))
    light_type = int(values[0])
    light = RecoveredLight(
        name=name,
        type=light_type,
        pos=(values[1], values[2], values[3]),
        dir=(values[4], values[5], values[6]),
        radius=values[7],
        color=(values[8], values[9], values[10]),
        intensity=values[11],
        line=line,
    )
    if len(values) >= 14:
        light.spot_inner = values[12]
        light.spot_outer = values[13]
    if "flags" in options:
        light.flags = int(options["flags"], 16)
    if "id" in options:
        light.light_id = int(options["id"], 0)
    if "motif" in options:
        light.motif = int(options["motif"], 0)
    return light


def _parse_light_fix(line: str, args: str) -> KeptLightFix:
    tokens = args.split()
    fix = KeptLightFix(type=int(tokens[0]), key=(float(tokens[1]), float(tokens[2]), float(tokens[3])), line=line)
    for token in tokens[4:]:
        if token == "remove":
            fix.remove = True
        elif token.startswith("or="):
            fix.or_flags |= int(token[3:], 16)
        elif token.startswith("clear="):
            fix.clear_flags |= int(token[6:], 16)
        elif token.startswith("dir="):
            parts = token[4:].split(",")
            fix.dir = (float(parts[0]), float(parts[1]), float(parts[2]))
    return fix


def _parse_matref(line: str, args: str) -> MaterialRef | None:
    m = _MATREF_RE.match(args)
    if m is None:
        return None
    return MaterialRef(volume=int(m.group(1)), material=int(m.group(2)), texture=m.group(3) or "", line=line)


def _parse_colors(args: str) -> ColorRun:
    tokens = args.split()
    colors = []
    for token in tokens[2:]:
        value, _, count = token.partition("*")
        rgb = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
        colors.extend([rgb] * (int(count) if count else 1))
    return ColorRun(segment=tokens[0], first_vertex=int(tokens[1]), colors=colors)


def _parse_order(args: str, out: list):
    for token in args.split():
        base, _, count = token.partition("+")
        v, m, c, t = (int(x) for x in base.split("."))
        for i in range(int(count) if count else 1):
            out.append((v, m, c, t + i))


def parse_file(path) -> LightmapRecoveryData:
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    data = LightmapRecoveryData(path=path, world=path.stem, text=text)
    lines = text.splitlines()

    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        if index == 0 and line.startswith("#") and not line.startswith("#!"):
            m = _HEADER_RE.match(line)
            if m is not None:
                data.world = m.group("world").strip()
                data.floor = _parse_rgb_slash(m.group("floor"))
                if m.group("h"):
                    data.sky_horizon = _parse_rgb_slash(m.group("h"))
                    data.sky_zenith = _parse_rgb_slash(m.group("z"))
                continue

        if line.startswith("#! "):
            directive, _, args = line[3:].partition(" ")
            args = args.strip()
            if directive == "sha256":
                data.sha256 = args.upper()
            elif directive == "from":
                data.source = args
            elif directive == "light":
                data.light_fixes.append(_parse_light_fix(line, args))
            elif directive == "aid":
                key, _, value = args.partition("=")
                data.aid.append((key.strip(), value.strip()))
            elif directive == "clear":
                ref = _parse_matref(line, args)
                if ref is not None:
                    data.clear_materials.append(ref)
                else:
                    m = _OBJREF_RE.match(args)
                    if m is not None:
                        data.clear_objects.append(ObjectRef(index=int(m.group(1)), mesh=m.group(2) or "", line=line))
                    else:
                        data.unknown.append(line)
            elif directive in ("vertrad", "novertrad"):
                ref = _parse_matref(line, args)
                if ref is not None:
                    (data.vertrad if directive == "vertrad" else data.novertrad).append(ref)
                else:
                    data.unknown.append(line)
            elif directive == "area":
                tokens = args.split()
                m = _MATREF_RE.match(tokens[0]) if tokens else None
                if m is not None and len(tokens) >= 6:
                    rgbi = tuple(float(x) for x in tokens[-4:])
                    texture = tokens[1] if len(tokens) >= 7 else ""
                    data.areas.append(AreaLight(int(m.group(1)), int(m.group(2)), texture, rgbi, line))
                else:
                    data.unknown.append(line)
            elif directive == "arealight":
                data.arealights.append(args)
            elif directive == "colors":
                data.colors.append(_parse_colors(args))
            elif directive == "order":
                _parse_order(args, data.order)
            elif directive == "apetris":
                data.apetris.append(args)
            else:
                data.unknown.append(line)
            continue

        if line.startswith("#"):
            data.notes.append(line[1:].strip())
            continue

        try:
            data.lights.append(_parse_light(line))
        except (ValueError, IndexError):
            data.unknown.append(line)

    return data


def find_file(world_name: str, search_dirs) -> Path | None:
    """The recovery file for a world (matched by name, case-insensitively) in the first folder that has one."""
    wanted = world_name.lower() + ".txt"
    for folder in search_dirs:
        if not folder:
            continue
        folder = Path(folder)
        if not folder.is_dir():
            continue
        candidate = folder / wanted
        if candidate.is_file():
            return candidate
        for child in folder.iterdir():
            if child.is_file() and child.name.lower() == wanted:
                return child
    return None


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ---------------------------------------------------------------------------------------------------------------------
# Applying it to a parsed world
# ---------------------------------------------------------------------------------------------------------------------

@dataclass
class RecoveryResult:
    data: LightmapRecoveryData
    exact: bool                                         # the file is for these exact bytes (its sha256 matched)
    lights: list[RecoveredLight] = field(default_factory=list)          # to create (floor ambient included)
    ambient_star_commands: list[str] = field(default_factory=list)      # for the world's own ambient
    ambient_props: dict = field(default_factory=dict)
    shape_star_commands: dict[int, list[str]] = field(default_factory=dict)  # worldshape index -> commands
    material_star_commands: dict[tuple[int, int], list[str]] = field(default_factory=dict)  # (mesh, material) -> added
    face_order: dict[tuple[int, int], list[int]] = field(default_factory=dict)  # (mesh, parsed mesh) -> rank per face
    art_colors: dict[tuple[int, int], dict[int, tuple[int, int, int]]] = field(default_factory=dict)  # -> {vert: rgb}
    aid_lines: list[str] = field(default_factory=list)
    report: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _material_texture(material) -> str:
    layer0 = material.get_register_value(SurfaceShaderRegisterType.LAYER0)
    return layer0.texture_name if layer0 is not None else ""


def _material_has_lightmap(material) -> bool:
    count = material.get_register_value(LightShaderRegisterType.LMCOUNT)
    return isinstance(count, int) and count > 0


def _add_star_command(material, name: str, *args):
    for command in material.star_commands:
        if command.name.lower() == name.lower():
            return False
    material.star_commands.append(StarCommand(name, *args))
    return True


def _varied_colors(model, material_index: int) -> bool:
    # unpasm's test for a vertex radiosity lit material: more than four colours on its vertices
    colors = set()
    for mesh in model.meshes:
        if not mesh.material_indices or mesh.material_indices[0] != material_index or not mesh.colors:
            continue
        for vertex_colors in mesh.colors:
            if not vertex_colors:
                continue
            c = vertex_colors[0]
            colors.add((round(c[0] * 255), round(c[1] * 255), round(c[2] * 255)))
            if len(colors) > 4:
                return True
    return False


def _lookup_material(world, ref, exact: bool, result: RecoveryResult, what: str):
    if ref.volume >= len(world.meshes) or ref.material >= len(world.meshes[ref.volume].materials):
        result.warnings.append(f"{what}: vol{ref.volume:02d}:{ref.material:03d} is not in this world")
        return None
    material = world.meshes[ref.volume].materials[ref.material]
    texture = _material_texture(material)
    if ref.texture and texture.strip().lower() != ref.texture.strip().lower():
        if not exact:
            result.warnings.append(f"{what}: vol{ref.volume:02d}:{ref.material:03d} is {texture}, not {ref.texture}: skipped")
            return None
        result.warnings.append(f"{what}: vol{ref.volume:02d}:{ref.material:03d} is {texture}, the file says {ref.texture}")
    return material


def _apply_material_flags(data: LightmapRecoveryData, world, exact: bool, result: RecoveryResult):
    # What unpasm's decompiler would flag (Decompile._LightMapFlags): in a lightmapped world, a material pasm could
    # have lit (not additive) but didn't was kept from the lightmaps (*notinlm), or vertex radiosity lit when its
    # colours vary (*vertrad); the file's "vertrad" / "novertrad" lines correct that judgement where it is wrong...
    flags: dict[tuple[int, int], int] = {}
    world_lightmapped = any(_material_has_lightmap(m) for model in world.meshes for m in model.materials)
    if world_lightmapped:
        for v, model in enumerate(world.meshes):
            for i, material in enumerate(model.materials):
                if _material_has_lightmap(material) or material.surface_shader.name.startswith("ADD_"):
                    continue
                flags[(v, i)] = APE_MAT_DO_NOT_LM | (APE_MAT_VERT_RADIOSITY if _varied_colors(model, i) else 0)

    for ref in data.vertrad:
        if _lookup_material(world, ref, exact, result, "vertrad") is not None:
            flags[(ref.volume, ref.material)] = flags.get((ref.volume, ref.material), 0) | APE_MAT_DO_NOT_LM | APE_MAT_VERT_RADIOSITY
    for ref in data.novertrad:
        if _lookup_material(world, ref, exact, result, "novertrad") is not None:
            flags[(ref.volume, ref.material)] = (flags.get((ref.volume, ref.material), 0) | APE_MAT_DO_NOT_LM) & ~APE_MAT_VERT_RADIOSITY
    for ref in data.clear_materials:
        if _lookup_material(world, ref, exact, result, "clear") is not None:
            flags[(ref.volume, ref.material)] = flags.get((ref.volume, ref.material), 0) | APE_MAT_DO_NOT_BLOCK_LM

    counts = {STAR_NOTINLM: 0, STAR_VERTRAD: 0, STAR_NOLMBLOCK: 0}

    def add(v, i, name, *args):
        if _add_star_command(world.meshes[v].materials[i], name, *args):
            result.material_star_commands.setdefault((v, i), []).append(str(StarCommand(name, *args)))
            if name in counts:
                counts[name] += 1

    for (v, i), f in sorted(flags.items()):
        if f & APE_MAT_VERT_RADIOSITY:
            add(v, i, STAR_VERTRAD)
        elif f & APE_MAT_DO_NOT_LM:
            add(v, i, STAR_NOTINLM)
        if f & APE_MAT_DO_NOT_BLOCK_LM:
            add(v, i, STAR_NOLMBLOCK)

    for area in data.areas:
        ref = MaterialRef(area.volume, area.material, area.texture)
        if _lookup_material(world, ref, exact, result, "area") is not None:
            add(area.volume, area.material, STAR_AREA_LIGHT, *(int(round(x)) for x in area.rgbi))

    result.report.append(
        f"world materials: {counts[STAR_NOLMBLOCK]} *{STAR_NOLMBLOCK}, {counts[STAR_VERTRAD]} *{STAR_VERTRAD}, "
        f"{counts[STAR_NOTINLM]} *{STAR_NOTINLM}" + (f", {len(data.areas)} area lights" if data.areas else ""))


def _apply_objects(data: LightmapRecoveryData, world, exact: bool, result: RecoveryResult):
    # "obj<NNN>" counts the world's static mesh placements in order (unpasm LmRecovery.FromStore)
    static_shapes = [
        i for i, shape in enumerate(world.worldshapes)
        if shape.type == WorldShapeType.MESH and shape.shape is not None and shape.shape.mesh_name
        and (shape.shape.mesh_inst_flags & MESH_INST_FLAG_STATIC) != 0
    ]
    applied = 0
    for ref in data.clear_objects:
        if ref.index >= len(static_shapes):
            result.warnings.append(f"clear: obj{ref.index:03d} ({ref.mesh}) is not in this world")
            continue
        shape_index = static_shapes[ref.index]
        mesh_name = world.worldshapes[shape_index].shape.mesh_name
        if ref.mesh and mesh_name.lower() != ref.mesh.lower():
            if not exact:
                result.warnings.append(f"clear: obj{ref.index:03d} is {mesh_name}, not {ref.mesh}: skipped")
                continue
            result.warnings.append(f"clear: obj{ref.index:03d} is {mesh_name}, the file says {ref.mesh}")
        commands = result.shape_star_commands.setdefault(shape_index, [])
        if STAR_NOLMUSE not in commands:
            commands.append(STAR_NOLMUSE)
            applied += 1
    result.report.append(f"placed objects: {applied} *{STAR_NOLMUSE}")


def _light_game_pos(light):
    # ParsedLight.pos is in Blender's axes; the file's are the game's
    return (light.pos[0], light.pos[2], light.pos[1])


def _light_game_dir(light):
    # The light's front (direction) is the second column of ParsedLight.mtx_orientation, in Blender's axes
    m = light.mtx_orientation
    return (m[0][1], m[2][1], m[1][1])


def _close(a, b, tolerance):
    return all(abs(x - y) <= tolerance for x, y in zip(a, b))


def _normalized(v):
    length = sum(x * x for x in v) ** 0.5
    return tuple(x / length for x in v) if length > 1e-12 else tuple(v)


def _apply_light_fixes(data: LightmapRecoveryData, world, result: RecoveryResult):
    kept = list(world.vis_data.lights)
    for model in world.meshes:
        kept.extend(model.lights or [])

    applied = 0
    for fix in data.light_fixes:
        if fix.type == APE_LIGHT_AMBIENT:
            if not _close(world.vis_data.ambient_light_color, fix.key, _COLOR_TOLERANCE):
                result.warnings.append(f"light: no ambient of colour {fix.key} (this world's is {tuple(round(c, 4) for c in world.vis_data.ambient_light_color)})")
                continue
            # (the compiled ambient is an engine light; "or=0x20": the bake read it too, i.e. it was *lm)
            for command in light_star_commands(fix.or_flags):
                if command not in result.ambient_star_commands:
                    result.ambient_star_commands.append(command)
            result.ambient_props["ape_flags_or"] = fix.or_flags
            result.ambient_props["ape_flags_clear"] = fix.clear_flags
            if fix.remove:
                result.ambient_props["removed"] = True
            applied += 1
            continue

        light_type = _APE_TO_LIGHT_TYPE.get(fix.type)
        if light_type == LightType.DIRECTIONAL:
            match = [l for l in kept if l.type == light_type and _close(_normalized(_light_game_dir(l)), _normalized(fix.key), _DIR_TOLERANCE)]
        else:
            match = [l for l in kept if l.type == light_type and _close(_light_game_pos(l), fix.key, _POS_TOLERANCE)]
        if not match:
            result.warnings.append(f"light: no kept light for '{fix.line}'")
            continue
        for light in match:
            if light.extra_star_commands is None:
                light.extra_star_commands = []
            if light.extra_props is None:
                light.extra_props = {}
            if fix.or_flags:
                for command in light_star_commands(fix.or_flags):
                    if command not in light.extra_star_commands:
                        light.extra_star_commands.append(command)
                light.extra_props["ape_flags_or"] = fix.or_flags
            if fix.clear_flags:
                light.extra_props["ape_flags_clear"] = fix.clear_flags
            if fix.dir is not None:
                # (the same direction as the compiled light's, but with the length the source wrote)
                light.extra_props["direction"] = list(fix.dir)
            if fix.remove:
                light.skip = True
        applied += 1
    if data.light_fixes:
        result.report.append(f"kept lights: {applied} of {len(data.light_fixes)} fixes applied")


def _apply_lights(data: LightmapRecoveryData, result: RecoveryResult):
    result.lights.extend(data.lights)
    if max(data.floor) > 0:
        # The floor as an ambient *onlylm light, half a 5/6/5 step up so it stores the same (unpasm LmRecovery._Ambient)
        q = (4, 2, 4)
        color = tuple(min(1.0, (f + (q[i] if f > 0 else 0)) * 2.0 / 255.0) for i, f in enumerate(data.floor))
        result.lights.append(RecoveredLight(
            name="lmambient", type=APE_LIGHT_AMBIENT, pos=(0.0, 0.0, 0.0), dir=(0.0, 0.0, 0.0), radius=0.0,
            color=color, intensity=1.0, flags=DEFAULT_LIGHTMAP_LIGHT_FLAGS, light_id=0xFFFF, line="(floor)"))
    by_type = {t: sum(1 for l in result.lights if l.type == t) for t in (0, 1, 2, 3)}
    result.report.append(
        f"lightmap-only lights: {len(result.lights)} ({by_type[1]} omni, {by_type[0]} spot, {by_type[2]} sun, {by_type[3]} ambient)")


def _apply_aid(data: LightmapRecoveryData, result: RecoveryResult):
    result.aid_lines = [f"{key}={value}" for key, value in data.aid]
    if max(data.sky_horizon) > 0 or max(data.sky_zenith) > 0:
        result.report.append(f"sky (header): horizon {data.sky_horizon}, zenith {data.sky_zenith}")
    if result.aid_lines:
        result.report.append(f".aid: {len(result.aid_lines)} settings (light_map_mbs is not stored: work it out for the texel size)")


def _apply_order(data: LightmapRecoveryData, world, result: RecoveryResult):
    # Each token is a compiled triangle, listed in the source's order; pasm seeds its lightmap charts in that order.
    # Every face gets its rank (ones the list leaves out go after, in their compiled order), and each mesh's faces
    # are sorted by it...
    if not data.order:
        return
    rank = {key: i for i, key in enumerate(data.order)}
    total = len(data.order)
    missing = 0
    unmatched = set(rank)
    for v, model in enumerate(world.meshes):
        for p, mesh in enumerate(model.meshes):
            if mesh.source_triangle_indices is None or mesh.cluster_index is None or not mesh.faces:
                continue
            ranks = []
            for f, tri in enumerate(mesh.source_triangle_indices):
                key = (v, mesh.material_indices[f], mesh.cluster_index, tri)
                r = rank.get(key)
                if r is None:
                    r = total + missing
                    missing += 1
                else:
                    unmatched.discard(key)
                ranks.append(r)
            order = sorted(range(len(ranks)), key=lambda i: ranks[i])
            mesh.faces = [mesh.faces[i] for i in order]
            mesh.material_indices = [mesh.material_indices[i] for i in order]
            mesh.source_triangle_indices = [mesh.source_triangle_indices[i] for i in order]
            result.face_order[(v, p)] = [ranks[i] for i in order]
    result.report.append(f"triangle order: {total - len(unmatched)} of {total} source-ordered triangles placed"
                         + (f", {missing} not in the list (placed last)" if missing else ""))
    if unmatched:
        result.warnings.append(f"triangle order: {len(unmatched)} listed triangles are not in this world")


def segment_vertex_map(model) -> tuple[dict[int, list[tuple[int, int]]], dict[int, int]]:
    """unpasm's numbering of a world mesh's decompiled segment vertices: number -> [(parsed mesh index, vertex index)],
    and the numbers of the vertex copies it makes (copy -> the number it copies).

    unpasm numbers a segment's vertices by first use: its materials in order, their clusters, each cluster's triangles
    (degenerate list triangles included), each triangle's corners; a vertex is its vertex buffer and index there.
    After each material's triangles it writes them out, and a triangle on the same three vertices as one written
    before (in the segment) gets three new copies of them (Decompile.DecompileSegments, TrisSeen): those take the
    next numbers, so they're counted here (they have no vertex of their own in Blender)."""
    numbering: dict[tuple[int, int], int] = {}
    copies: dict[int, int] = {}                 # copy's number -> the number of the vertex it copies
    next_number = 0
    tris_seen: set[tuple[int, int, int]] = set()
    by_material: list[list] = []
    for mesh in model.meshes:
        if mesh.source_corner_sequence is None:
            return {}, {}
        material = mesh.material_indices[0] if mesh.material_indices else -1
        if not by_material or by_material[-1][0] != material:
            by_material.append([material, []])
        by_material[-1][1].append(mesh)
    for _, meshes in by_material:
        triangles = []
        for mesh in meshes:
            numbers = []
            for index in mesh.source_corner_sequence:
                key = (mesh.vb_index, index)
                number = numbering.get(key)
                if number is None:
                    number = numbering[key] = next_number
                    next_number += 1
                numbers.append(number)
            triangles.extend(tuple(sorted(numbers[i:i + 3])) for i in range(0, len(numbers) - 2, 3))
        for triangle in triangles:
            if triangle in tris_seen:
                for k in range(3):
                    copies[next_number + k] = triangle[k]
                next_number += 3
            else:
                tris_seen.add(triangle)
    out: dict[int, list[tuple[int, int]]] = {}
    for p, mesh in enumerate(model.meshes):
        for local, index in enumerate(mesh.source_vertex_indices):
            number = numbering.get((mesh.vb_index, index))
            if number is not None:
                out.setdefault(number, []).append((p, local))
    return out, copies


def segment_names(world) -> dict[str, int]:
    """unpasm's segment name for each world mesh: "volNN" after the first volume using it, else "meshNN"."""
    names = {}
    for m in range(len(world.meshes)):
        volume = next((i for i, vol in enumerate(world.vis_data.volumes) if vol.world_geo_index == m), -1)
        names[f"vol{volume:02d}" if volume >= 0 else f"mesh{m:02d}"] = m
    return names


def _apply_colors(data: LightmapRecoveryData, world, result: RecoveryResult):
    # The art's colours of vertex radiosity vertices (the compiled world holds pasm's baked ones; pasm adds its light
    # to the art's, so the baked ones would bake twice)...
    if not data.colors:
        return
    segments = segment_names(world)
    runs_by_mesh: dict[int, list[ColorRun]] = {}
    for run in data.colors:
        v = segments.get(run.segment)
        if v is None:
            result.warnings.append(f"colors: no segment {run.segment}")
            continue
        runs_by_mesh.setdefault(v, []).append(run)

    placed = copied = missing = vertices = 0
    for v, runs in runs_by_mesh.items():
        model = world.meshes[v]
        vmap, copies = segment_vertex_map(model)
        colors: dict[tuple[int, int], dict[int, tuple[int, int, int]]] = {}
        seg_placed = seg_copied = seg_missing = seg_vertices = 0
        on_lightmapped = 0
        for run in runs:
            for i, rgb in enumerate(run.colors):
                seg_vertices += 1
                number = run.first_vertex + i
                if number in copies:
                    seg_copied += 1
                    continue
                targets = vmap.get(number)
                if not targets:
                    seg_missing += 1
                    continue
                seg_placed += 1
                for p, local in targets:
                    material = model.materials[model.meshes[p].material_indices[0]]
                    if _material_has_lightmap(material):
                        on_lightmapped += 1
                    colors.setdefault(p, {})[local] = rgb
        vertices += seg_vertices
        # (vertex radiosity vertices are never on a lightmapped material: if some land there, this segment's
        # vertices aren't numbered as unpasm numbered them, and none of its colours can be trusted)
        if on_lightmapped or seg_missing:
            result.warnings.append(
                f"colors: {runs[0].segment}'s vertices don't line up with unpasm's numbering "
                f"({on_lightmapped} land on lightmapped materials, {seg_missing} not found): its {seg_vertices} colours left out, the baked ones kept")
            missing += seg_vertices
            continue
        placed += seg_placed
        copied += seg_copied
        for p, cmap in colors.items():
            result.art_colors[(v, p)] = cmap
    result.report.append(f"vertex radiosity art colours: {placed} of {vertices} vertices placed"
                         + (f" ({copied} more are unpasm's copies for repeated triangles)" if copied else "")
                         + (f", {missing} left out" if missing else ""))


def apply(data: LightmapRecoveryData, world, exact: bool) -> RecoveryResult:
    """Puts the file's data into the parsed world (in place) and returns what the builders still do.

    exact: the file's sha256 is the world's. Without it, only what can be checked against the world by name or
    position is applied (lights, .aid lines, fixes to kept lights, materials and objects whose texture / mesh names
    match); the triangle order and vertex colours, which go by index only, are left out."""
    result = RecoveryResult(data=data, exact=exact)
    result.report.append(f"{data.path.name}: {data.source}" if data.source else data.path.name)
    _apply_lights(data, result)
    _apply_light_fixes(data, world, result)
    _apply_aid(data, result)
    _apply_material_flags(data, world, exact, result)
    _apply_objects(data, world, exact, result)
    if exact:
        _apply_order(data, world, result)
        _apply_colors(data, world, result)
    else:
        if data.order or data.colors:
            result.warnings.append("not the world this file was made for (sha256 differs): triangle order and vertex colours left out")
    if data.apetris:
        result.warnings.append(f"{len(data.apetris)} '#! apetris' hand edits are not applied (replay them with unpasm apetris)")
    if data.arealights:
        result.report.append(f"{len(data.arealights)} area lights with no compiled material (kept as data, not applied)")
    for line in data.unknown:
        result.warnings.append(f"not understood: {line}")
    return result
