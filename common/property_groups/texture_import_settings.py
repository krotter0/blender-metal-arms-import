import bpy
from pathlib import Path
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty

class TextureImportSettings(PropertyGroup):
    load_textures: BoolProperty(
        name="Load Textures",
        description="Load textures used by the .ape to the scene from an external directory.",
        default=False
    )

    texture_folder_path: StringProperty(
        name="Texture Folder Path",
        description="Path to the folder containing textures used by the .ape.",
        default="",
        subtype='DIR_PATH',
        update=lambda self, _: setattr(self, "texture_folder_valid", Path(self.texture_folder_path).is_dir())
    )

    texture_allow_recurse: BoolProperty(
        name="Check subfolders",
        description="Whether to also load textures from subfolders of the specified texture folder.",
        default=True
    )

    texture_folder_valid: bpy.props.BoolProperty(
        name="Texture Folder Valid",
        default=False,
        options={'HIDDEN'},
    )

    def draw(self, context, layout):
        row = layout.row()
        row.prop(self, "load_textures")
        row = layout.row()
        row.enabled = self.load_textures
        row.alert = not self.texture_folder_valid
        row.prop(self, "texture_folder_path")
        row.prop(self, "texture_allow_recurse")

    def is_valid(self):
        return not self.load_textures or Path(self.texture_folder_path).is_dir()
    
    def get_path(self):
        if not self.load_textures:
            return None
        return self.texture_folder_path