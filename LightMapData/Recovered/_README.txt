Lightmap data for each world: what pasm's bake read from a world's source that the compiled world in the
master file no longer holds. One file a world, made 11/18/2026 by `unpasm lmdata` from the sources in
3dsAttempt\unpasm_out (the 44 campaign worlds: the designers' exported .wld; the 14 multiplayer worlds: the lights
fitted and refined against retail's lightmaps).

Use: `unpasm worlds <retail master> <out folder> [<world>...] --recover` reads <world>.txt from the folder named in
UNPASM_STORE (or from Recovered\ beside unpasm.exe) when its "#! sha256" is the retail world's, and writes the
world's .wld and .aid with this data put back.

A file's lines:
  # <world>: floor 0/0/0; sky h 0/0/0 z 0/0/0   header (the floor and sky are in the lights and the .aid lines here)
  #! sha256 <hash>                               the retail world these answers are for
  #! from <text>                                 where the data came from
  # ...                                          notes: counts from the comparison with the master alone
  #! aid <key>=<value>                           a line of the world's .aid (budget, sky light, quality)
  #! light <type> <x> <y> <z> or=0x20            a light the compiled world keeps that the bake also read (a sun: its
                                                 direction; an ambient: its colour)
  #! light <type> <x> <y> <z> dir=<dx,dy,dz>      that light's direction vector as the source writes it: pasm's spot
                                                 cone uses it as is, and the exporter wrote some ~2.4 long (Rocket 1)
  #! order <vol>.<mtl>.<cluster>.<tri>[+<n>] ... the source's triangle order, as the compiled world's triangles (pasm
                                                 seeds its lightmap charts in source order); worlds --recover sorts the
                                                 decompiled triangles into it
  #! clear vol<NN>:<MMM> <texture>               a world material that did not block light (*nolmblock / *nolmuse)
  #! clear obj<NNN> <mesh>                       a placed object left out of the bake (*nolmuse)
  #! vertrad vol<NN>:<MMM> <texture>             an unlit world material that IS lit by vertex radiosity (*vertrad),
                                                 where the decompiler, going by its colours, would say it isn't
  #! novertrad vol<NN>:<MMM> <texture>           one that is NOT (*notinlm, or left unlit by pasm), where the decompiler
                                                 would say it is; its colours are the art's already
  #! area volNN:MM <texture> r g b i             a compiled world material's area light (from the source's LightRGBI); applied
  #! arealight <seg> <tex> r g b i x y z         an area light on no compiled material; kept as data, not applied
                                                 (none left: lmdata leaves out area lights on materials pasm's
                                                 lightmapper skips, NO_DRAW or NO_LM_USE without VERT_RADIOSITY,
                                                 which no bake had; Night Sneak 1's two lamps were such, 11/20)
  #! apetris <arguments>                         a triangle edit made by hand, replayed through `unpasm apetris`
  <name> <type> x y z dx dy dz radius r g b intensity [inner outer] [flags=0x..] [id=..] [motif=..]
                                                 a lightmap-only light (type 0 spot, 1 omni, 2 sun, 3 ambient;
                                                 "\s" in a name is a space); flags 0x30 when not given
  #! colors <segment> <first vertex> <rrggbb>[*count] ...
                                                 the art's colours of vertex radiosity vertices, one after another
                                                 from that vertex of the decompiled segment (the compiled world holds
                                                 the baked colours; pasm bakes light + art, so they must not stay)

A world material with a lightmap in retail needs no flag; one without is *notinlm, and *vertrad too when its colours
vary or a "#! vertrad" line says so.

The multiplayer worlds have no source to take the art's colours from. Their "#! colors" are black, which is what
the designers gave such surfaces (99.2% of them in the campaign sources), or the campaign level's own where it
shares the geometry (`lmdata -artblack -artfrom`: 53 vertices of we05, from Research 4). Baked by pasm, we07's
vertex-lit surfaces then come out at 35.9 against retail's 35.3 (with retail's baked colours left in: 66.0).
The multiplayer sources in unpasm_out and the clean master were made before this (11/18) and still have the baked
colours; the sources these files give are in claude\scratchpads\session_1115\lmdata\mpblack_rt.

The files carry no light_map_mbs: worlds --recover works the budget out from the decompiled source's own area metric
(as pasm sums it) for retail's texel size. All of this needs unpasm_new2.exe (11/19) or later; made 11/19 by
claude\scratchpads\session_1115\lmdata\regen.sh.
