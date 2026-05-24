from dataclasses import dataclass

from .....common.star_command_assembler import StarCommand

from ...types.shaders import LightShader, LightShaderRegisterType, SurfaceShader, SurfaceShaderRegisterType, ToolShader

@dataclass
class ParsedTextureInstance:
    texture_name: str
    tex_layer_id: int

@dataclass
class ParsedMotif:
    motif_color: tuple[float, float, float]
    motif_index: int

@dataclass
class ParsedShaderRegister:
    value: int | float | ParsedTextureInstance | ParsedMotif

@dataclass
class ParsedMaterial:
    shader: ToolShader
    surface_shader: SurfaceShader
    light_shader: LightShader
    surface_registers: dict[SurfaceShaderRegisterType, ParsedShaderRegister]
    light_registers: dict[LightShaderRegisterType, ParsedShaderRegister]
    star_commands: list[StarCommand]
    tex_layer_count: int
    tint: tuple[float, float, float]

    def get_register(self, register_type: SurfaceShaderRegisterType | LightShaderRegisterType):
        if isinstance(register_type, SurfaceShaderRegisterType):
            return self.surface_registers.get(register_type, None)
        elif isinstance(register_type, LightShaderRegisterType):
            return self.light_registers.get(register_type, None)
        else:
            raise ValueError(f"Invalid register type: {register_type}")

    def get_register_value(self, register_type: SurfaceShaderRegisterType | LightShaderRegisterType):
        register = self.get_register(register_type)
        return register.value if register is not None else None