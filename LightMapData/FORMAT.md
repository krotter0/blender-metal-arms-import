# unpasm's lightmap data files: what they are and their format

Copied 11/20/2026 from `D:\unpasm-source\Code\unpasm\Recovered\` (the live set, as used by the current `unpasm.exe`).

## What this data is for

A compiled Metal Arms world in the Xbox master (`retailxbox.mst`) keeps its baked lightmaps but not most of what pasm's
lightmapper read to bake them. The source `.wld` had lightmap-only lights, materials and placed objects marked as not
blocking light, vertex colours, bake settings and a triangle order; pasm strips or overwrites all of these when it
compiles. unpasm can decompile the world's geometry, objects and kept lights from the master alone, but to make pasm
bake the same lightmaps again it needs that lost data back.

Each file here is that lost data for one world: `Recovered\<world>.txt`, 58 files, one per world in the game
(44 campaign, 14 multiplayer), plus `_README.txt` (the short version of this document).

- **Campaign worlds (44):** taken from the designers' own Max-exported `.wld` sources by `unpasm lmdata` (11/18-19),
  i.e. what the designers actually set. Since 11/20 a few have hand corrections where retail's lightmaps showed the
  shipped bake differed from the designers' source (each marked with a `# 11/20:` note line; see below).
- **Multiplayer worlds (14):** no sources exist. Their lights were fitted and refined against retail's lightmaps over
  many test bakes (11/13-11/20); their vertex colours are black, as the designers used for such surfaces.

## How unpasm uses it

```
unpasm worlds <retail master> <out folder> [<world>...] --recover
```

For each world, unpasm looks for `<world>.txt` in the folder named by the environment variable `UNPASM_STORE`, or
else in `Recovered\` beside `unpasm.exe`. A file is used only if its `#! sha256` line equals the SHA-256 of the
world's compiled entry in the master given; otherwise (or with no file) unpasm falls back to fitting lights from the
master's lightmaps alone (`LmRecovery.Run`), which is far less exact.

With a matching file, `worlds --recover`:

1. decompiles the world from the master, with the file's lightmap-only lights added, its `#! clear` materials marked
   `DO_NOT_BLOCK_LM` and objects marked `*nolmuse`, and its `#! vertrad` / `#! novertrad` overrides applied;
2. puts the stored art colours on the vertex radiosity vertices (`#! colors`; the baked ones go to `_vertrad.txt`);
3. applies the `#! light` fixes to lights the compiled world kept;
4. replays the `#! apetris` triangle edits;
5. sorts the triangles into the stored source order (`#! order`);
6. works out the lightmap budget (`light_map_mbs`) from the result's own area metric, as pasm sums it, so the texel
   size comes out as retail's;
7. writes `<world>.wld` and `<world>.aid` (the `.aid` gets the measured settings, the sky from the header, and every
   `#! aid` line, a stored key replacing a measured one), plus reports in `Worlds\<world>\` (`_recover.txt`,
   `_lights.txt`, `_vertrad.txt`, `_instlight.txt`).

## The format

Plain text, one item per line, CRLF line ends (unpasm keeps whichever it finds). Numbers use `.` as the decimal point.
Lines starting with `#! ` are data; other lines starting with `#` are notes and ignored, except the header. Every
other non-empty line is a light. Line order does not matter except that lights keep their order (pasm processes
lights in order) and `#! order` lines are read in order.

### Header (first line)

```
# we09multi09: floor 0/0/0; sky h 0/0/0 z 0/0/0
```

- `floor r/g/b` (0-255): a lightmap ambient; when not 0/0/0 it is added as an ambient `*onlylm` light named `lmambient`.
- `sky h r/g/b z r/g/b`: pasm's sky light (horizon and zenith colours); none when all near 0. Most files leave both
  at 0 and give the sky as `#! aid light_map_skylight_*` lines instead.

### Identity and provenance

```
#! sha256 50887E1EEB45B2EA04FA8771025B8317D042D656A78E88FC5A4C4947BB0F888F
#! from the designers' source .wld and .aid (unpasm_out before 11/18 22:17), 11/19
# 11/20: the four LastHall*onlylm lamps at (-655.0, 256.5), ... x0.7 (0.8 -> 0.56) to retail's lightmaps (...)
```

- `#! sha256 <hex>`: the SHA-256 of the world's compiled entry in the retail master. The file is used only for that
  exact world.
- `#! from <text>`: where the data came from (shown in unpasm's report).
- `# <text>`: notes. Lines `# lights: ...`, `# objects: ...`, `# not blocking: ...` etc. are counts from comparing the
  source with the master alone, written by `lmdata`. Lines `# 11/20: ...` record a hand correction made on 11/20 (what
  changed, why, and the pasm test builds and scores that justified it).

### Lightmap-only lights (lines without `#`)

```
<name> <type> <x> <y> <z> <dx> <dy> <dz> <radius> <r> <g> <b> <intensity> [<inner> <outer>] [flags=0x..] [id=..] [motif=..]
Omni05*onlylm 1 287.943848 13.0687609 -68.08633 0 0 0 115.158752 0.376470625 0.8745099 0.964705944 0.8
StreetSpot*only 0 -211.833755 -171.066132 605.2189 -0.2091201 -0.9778877 0.00171366264 140.000031 0.976 0.965 0.651 2 0.34906584 1.08210409
moonlight*onlyl 2 0 0 0 -0.144543946 -0.9396926 -0.3099755 0 0.1764706 0.168627456 0.329411775 1.2
ambient 3 0 0 0 0 0 0 0 0.203921586 0.203921586 0.24313727 1
```

- `name`: the light's name as in the source (Max names; `*onlylm` / `*lm` are the designers' star commands, kept for
  reference). `\s` stands for a space, `\e` for an empty name, a leading `\h` for `#`. Fitted lights are `lmfitNNN`;
  lamps placed on fixtures by hand or by the fixture rule are `lamp...`.
- `type`: 0 spot, 1 omni (point), 2 sun (directional), 3 ambient.
- `x y z`: position (world units; 0 0 0 for suns and ambients).
- `dx dy dz`: direction (spots and suns). For a spot, pasm uses the vector as written, length included, in its cone
  test: some designers' spots were exported with a direction about 2.4 long, and that is kept.
- `radius`: range. **pasm takes any radius over 316.2 as 500** (CLightingSolution::AddLight), so large radii are not as
  far-reaching as their numbers say.
- `r g b`: colour, 0-1. `intensity`: multiplier. An omni's strength is about 2.85 x radius x intensity, a spot's 20
  times that.
- `inner outer` (spots only): the cone's full angles in radians.
- `flags=0x..` (hex), `id=..`, `motif=..`: the light's APE flags, light ID and motif when not the defaults (flags 0x30 =
  lightmap only).

### Kept lights' fixes

```
#! light 3 0.164705887 0.223529428 0.2627451 or=0x20
#! light 0 5369.778 -623.2701 7446.349 dir=-1.95594084,-0.907306552,0.905394554
```

`#! light <type> <a> <b> <c> <change>`: a light the compiled world still has, found by type and position (a sun by its
direction, an ambient by its colour, given as the three numbers), and a change: `or=0x..` sets flags (here: it was also
a lightmap light, which the compiled world no longer records), `clear=0x..` clears flags, `dir=dx,dy,dz` sets its
direction vector as the source wrote it, `remove` drops it.

### Bake settings

```
#! aid light_map_detail=3
#! aid light_map_skylight_detail=2
#! aid light_map_skylight_zenith_red=255
```

`#! aid <key>=<value>`: a line of the world's `.aid` (pasm's per-world bake settings) that a decompile cannot measure:
radiosity quality, sky light, sky detail and so on. The lightmap budget (`light_map_mbs`) is not stored; unpasm works
it out. Not recoverable and not stored: `light_map_subsample` (left at pasm's default, 0; checked 11/20, see below).

### Blockers

```
#! clear vol05:045 tecr_glas01
#! clear obj136 gowr4light1
```

- `#! clear vol<NN>:<MMM> <texture>`: world material `MMM` of volume (segment) `NN` does not block light in the bake
  (written as `DO_NOT_BLOCK_LM`; the designers' `*nolmblock` / `*nolmuse`). The texture name is for reading only.
- `#! clear obj<NNN> <mesh>`: placed object `NNN` is left out of the bake entirely (`*nolmuse`: casts no shadow and gets
  no baked light). `NNN` counts the world's static mesh placements in master order (`unpasm objlist <mst> <world>`
  lists them with positions).

### Vertex radiosity and vertex colours

```
#! vertrad vol01:001 tesstrian01
#! novertrad vol12:005 temh_xwal03
#! colors vol01 0 000000*2864
#! colors vol01 159 000000*3 010000 000000 010000 010110 000000 010110 010111 000000 ...
```

- `#! vertrad` / `#! novertrad vol<NN>:<MMM> <texture>`: whether an unlit world material is lit by vertex radiosity
  (`*vertrad`). Only written where the decompiler, judging by the master's colours, would get it wrong.
- `#! colors <segment> <first vertex> <rrggbb>[*count] ...`: the art's colours of vertex radiosity vertices, from that
  vertex of the decompiled segment on, run-length coded (`*count` repeats). The compiled world holds pasm's baked
  colours there instead; pasm adds its light to the art's, so leaving the baked ones in would bake them twice as
  bright. 99.2% of the designers' colours are black, and the multiplayer worlds use black.

### Triangle order

```
#! order 1.0.1.497 1.0.1.572 1.0.1.498+2 1.0.0.416+2 ...
```

Each token is a compiled triangle `<volume>.<material>.<cluster>.<triangle>` (`+n`: n consecutive ones), listed in the
order of the source's triangles. pasm seeds its lightmap charts in source order, so the order changes the bake;
unpasm sorts the decompiled triangles into it. Pieces of a source triangle that pasm cut at volume boundaries are
placed where their source triangle was. Long lists wrap over many `#! order` lines.

### Other

- `#! apetris <arguments>`: a hand edit of triangles, replayed through `unpasm apetris` (two files: we03 and we11,
  thin strips turned into vertex-lit pieces).
- `#! area volNN:MM <texture> r g b i`: a compiled world material's area light (the source material's `LightRGBI`),
  applied to that material by `worlds --recover`. No world in this set has one.
- `#! arealight <segment> <texture> r g b i x y z`: an area light on a source material that has no compiled material,
  kept as data and not applied. No file has one now. Night Sneak 1 had two (`areaLamp03`, `areaLamp11`), but both were
  invisible quads (star command NO_DRAW). pasm ORs the star flags into the material's flags (KongDef.cpp line 1172),
  and its lightmapper skips NO_DRAW world materials (LightMapGen.cpp, `LMG_StaticallyLightMaterial`). So no bake,
  retail's included, ever had their light. Since 11/20 `lmdata` leaves out area lights on materials the lightmapper
  skips: NO_DRAW, or NO_LM_USE without VERT_RADIOSITY. The world still comes out byte for byte the same.

## Counts in this set

58 world files, 8.3 MB. Directives over all files: 2041 `#! colors`, 1925 `#! order`, 1383 `#! vertrad`, 789
`#! clear`, 185 `#! aid`, 58 `#! sha256`, 58 `#! from`, 34 `#! light`, 20 `#! novertrad`, 2 `#! apetris`; plus every world's lightmap-only lights.

## Hand corrections made on 11/20 (all marked with a `# 11/20:` note)

All checked by baking in pasm against retail's lightmaps (RMS by triangle, lower is closer):

| World | Change | Score |
|---|---|---|
| Station 2 | four lamp pairs dimmed | 10.27 -> 6.47 |
| Station 1 | two warm lamp pairs dimmed | 5.97 -> 5.03 |
| Trace | the 13 pipe materials block again | 9.00 -> 7.67 |
| Research 4 | three lamp fixtures out of the bake, like the other 24 | 6.00 -> 5.30 |
| Comm 1 | a four-lamp cluster x0.7, then the sun x1.15 | 5.20 -> 4.63 |
| Research 3 | nine lower lamps x0.85 | 5.83 -> 5.67 |
| Invasion | moonlight x1.2 | 5.07 -> 4.20 |
| Town | 20 fill lamps x1.2 | 4.37 -> 4.23 |
| MP 14 | four stacked fitted lights cut to one; three fixtures' lights replaced by lamps on the fixtures | 15.70 -> 14.37 |
| MP 09 | seven fitted lights replaced by two lamps stacked on the wall lamp's axis | 15.90 -> 15.47 |
| MP 01 | 12 fitted lights replaced by 5 lamps on their fixtures | 16.23 -> 16.03 |

The previous versions of these files are in `D:\unpasm-source\Code\unpasm\Recovered_before_1120\`.

## Related files (in `related\`, also read by unpasm, not per world)

- `lmpass.csv`: `<mesh>,<texture>,<copy>` rows. A placed mesh that retail's bake let light through although its mask
  texture's corner blocks: `meshes` points the mesh at `<copy>`, `textures` writes the copy into `TGA\root`, where pasm's
  lightmapper does not look. One row: Ruins 1's glass object (`gocrbldgls1,tecr_glas01,tecr_glas1x`). Copy names must
  be under 12 characters (pasm refuses longer texture names).
- `standins.csv`: placed meshes the master lacks and what the game draws in their place (Research 1's RAT with its turret).

Also part of unpasm's behaviour, not a file: `textures` writes a transparency mask's top-left texel with no colour when
its alpha is 17 or less (pasm's lightmapper multiplies light by that texel's colour; retail's lightmaps show the light
passing). This fixed Ruins 1's lamp-post shadow blobs and Station 2's glow-card shadows.

## On the subsampling setting (11/20)

`light_map_subsample` is not in the compiled data, so every world bakes at pasm's default (0, which applies a 3x3 blur
as the bake's last step). Checked: City 1, Invasion, MP 06 and Coliseum 2 (the worlds whose lightmaps looked sharpest
against ours) baked with subsampling on came out 3-4 times further from retail (City 1 3.67 -> 12.1, Invasion 4.20 ->
10.4, MP 06 7.13 -> 17.5, Coliseum 2 1.70 -> 5.17), as did we01 on 11/14. A texel-sharpness comparison over all 58
worlds found no world standing apart.
