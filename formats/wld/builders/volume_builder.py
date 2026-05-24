import bpy
from . import cell_builder
from ..parsers.models.cells import ParsedCell
from ..parsers.models.volumes import ParsedVolume, ParsedVolume

def build(volume: ParsedVolume, cells: list[ParsedCell]):
    parent_collection = bpy.context.collection

    if volume.cell_count > 1:
        name = f"volume_{volume.volume_id}"
        collection = bpy.data.collections.new(name)
        parent_collection.children.link(collection)

        parent_collection = collection

    for i in range(volume.cell_first_idx, volume.cell_first_idx + volume.cell_count):
        cell = cells[i]
        cell_builder.build(cell, parent_collection, name=f"cell_{i}")
    