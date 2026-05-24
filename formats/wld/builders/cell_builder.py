import bpy
import math

from ..parsers.models.cells import ParsedCell
from ..types.world import FVisCell_t, FVisData_t, FVisPlane_t
from ....common import vec, axis_convert

def build(cell: ParsedCell, parent_collection: bpy.types.Collection = None, name = None):
    parent_collection = parent_collection or bpy.context.collection

    name = name or f"cell"

    vertices = cell.vertices
    faces = cell.plane_faces

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    parent_collection.objects.link(obj)

    obj.hide_set(True)

    mesh.from_pydata(vertices, [], faces)
    mesh.update()