import bpy
from bpy.props import PointerProperty

from .common.property_groups.texture_import_settings import TextureImportSettings
from .formats.ape.importer import ImportApe
from .formats.mtx.importer import ImportMtx
from .formats.wld.importer import ImportWld

def menu_func_import(self, context):
    self.layout.operator(ImportApe.bl_idname, text="Metal Arms Compiled Mesh (.ape)")
    self.layout.operator(ImportWld.bl_idname, text="Metal Arms Compiled World (.wld)")
    self.layout.operator(ImportMtx.bl_idname, text="Metal Arms Compiled Animation (.mtx)")

_CLASSES = [
    TextureImportSettings,
    ImportApe,
    ImportWld,
    ImportMtx,
]

_PROPERTY_GROUPS = {
    "ma_texture_import_settings": TextureImportSettings,
}

def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    for name, cls in _PROPERTY_GROUPS.items():
        setattr(bpy.types.WindowManager, name, PointerProperty(type=cls))
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    for cls in _CLASSES:
        bpy.utils.unregister_class(cls)
    for name in _PROPERTY_GROUPS.keys():
        delattr(bpy.types.WindowManager, name)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()