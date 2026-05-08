import bpy
from .formats.ape.importer import ImportApe
from .formats.mtx.importer import ImportMtx
from .formats.wld.importer import ImportWld

def menu_func_import(self, context):
    self.layout.operator(ImportApe.bl_idname, text="Metal Arms Compiled Mesh (.ape)")
    self.layout.operator(ImportWld.bl_idname, text="Metal Arms Compiled World (.wld)")
    self.layout.operator(ImportMtx.bl_idname, text="Metal Arms Compiled Animation (.mtx)")

def register():
    bpy.utils.register_class(ImportApe)
    bpy.utils.register_class(ImportWld)
    bpy.utils.register_class(ImportMtx)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportApe)
    bpy.utils.unregister_class(ImportWld)
    bpy.utils.unregister_class(ImportMtx)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()