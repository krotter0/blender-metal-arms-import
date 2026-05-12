from enum import Enum, Flag

from ..common.types.common import CFColorMotif
from .types.texture import FShTexInst_t

class FDX8VB_Info:
    def __init__(self,
        vtx_bytes: int,
        unlit: bool,
        normal_count: int,
        weight_count: int,
        color_count: int,
        tc_count: int,
        offset_pos: int,
        offset_weight: int,
        offset_norm: int,
        offset_color: int,
        offset_tc: int
    ):
        self.vtx_bytes = vtx_bytes
        self.unlit = unlit
        self.normal_count = normal_count
        self.weight_count = weight_count
        self.color_count = color_count
        self.tc_count = tc_count
        self.offset_pos = offset_pos
        self.offset_weight = offset_weight
        self.offset_norm = offset_norm
        self.offset_color = offset_color
        self.offset_tc = offset_tc
    
class LightShaderRegisterType(Enum):
    ZMASK = 0
    EMASK = 1
    SMASK = 2
    BUMPMAP = 3
    BUMPMAP_TILE_FACTOR = 4
    DMOTIF = 5
    EMOTIF = 6
    SMOTIF = 7
    SEXP = 8
    LMCOUNT = 9
    LM = 10
    LM_TC = 11
    LM_MOTIF = 12
    MAX = 13
    NULL = 255

class SurfaceShaderRegisterType(Enum):
    LAYER0 = 0
    TC0 = 1
    LAYER1 = 2
    TC1 = 3
    LAYER2 = 4
    TC2 = 5
    LAYER3 = 6
    TC3 = 7
    ENV_MOTIF = 8
    DETAILMAP = 9
    DETAILMAP_TILE_FACTOR = 10
    MAX = 11
    NULL = 255
    
    @staticmethod
    def layer(index: int):
        return SurfaceShaderRegisterType(index * 2)
    
    @staticmethod
    def tc(index: int):
        return SurfaceShaderRegisterType((index * 2) + 1)

class SurfaceShaderFlags(Flag):
    OPAQUE = 0x1
    CUTOUT = 0x2
    TRANSLUCENT = 0x4
    DETAIL_MAP = 0x8

class SurfaceShader(Enum):
    oBASE = 0
    cBASE = 1
    tBASE = 2
    etBASE = 3
    tBASE_ADD_SPEC = 4
    etBASE_ADD_SPEC = 5
    etBASE_ADD_bSPEC = 6
    ADD_BASE = 7
    oBASE_LERP_tLAYER = 8
    oBASE_LERP_vLAYER = 9
    oBASE_LERP_pLAYER = 10
    cBASE_LERP_tLAYER = 11
    cBASE_LERP_vLAYER = 12
    cBASE_LERP_pLAYER = 13
    tBASE_LERP_tLAYER = 14
    tBASE_ADD_SPEC_LERP_tLAYER = 15
    oBASE_ADD_rbENV = 16
    etBASE_ADD_rbENV = 17
        
    oBASE_DETAIL = 18
    cBASE_DETAIL = 19
    tBASE_DETAIL = 20
    etBASE_DETAIL = 21
    tBASE_ADD_SPEC_DETAIL = 22
    etBASE_ADD_SPEC_DETAIL = 23
    etBASE_ADD_bSPEC_DETAIL = 24
    ADD_BASE_DETAIL = 25
    oBASE_LERP_tLAYER_DETAIL = 26
    oBASE_LERP_vLAYER_DETAIL = 27
    oBASE_LERP_pLAYER_DETAIL = 28
    cBASE_LERP_tLAYER_DETAIL = 29
    cBASE_LERP_vLAYER_DETAIL = 30
    cBASE_LERP_pLAYER_DETAIL = 31
    tBASE_LERP_tLAYER_DETAIL = 32
    tBASE_ADD_SPEC_LERP_tLAYER_DETAIL = 33
    oBASE_ADD_rbENV_DETAIL = 34
    etBASE_ADD_rbENV_DETAIL = 35
        
    oBASE_ADD_rbSREFLECT = 36
        
    tBASE_vALPHA = 37

    LIQUID_ENV = 38
    LIQUID_LAYER_ENV = 39
    LIQUID_TEXTURE = 40
    LIQUID_MOLTEN_1LAYER = 41
    LIQUID_MOLTEN_2LAYER = 42

    oBASE_LERP_tLAYER_ADD_rbENV = 43
    oBASE_LERP_vLAYER_ADD_rbENV = 44
    oBASE_LERP_pLAYER_ADD_rbENV = 45
        
    oBASE_LERP_tLAYER_ADD_rbENV_DETAIL = 46
    oBASE_LERP_vLAYER_ADD_rbENV_DETAIL = 47
    oBASE_LERP_pLAYER_ADD_rbENV_DETAIL = 48

    pBASE = 49
    epBASE = 50
    pBASE_ADD_SPEC = 51
    epBASE_ADD_SPEC = 52
    epBASE_ADD_bSPEC = 53
    ADD_vBASE = 54
        
    LIGHT_MORPH = 55

    DECAL_AI = 56
    DECALTEX_AI = 57
    DECALTEX_AT = 58
    DIFFUSETEX_AI = 59
    DIFFUSETEX_AT = 60
    DIFFUSETEX_AIAT = 61
    SPECULARTEX_AT = 62
    ADD = 63
    BLEND_AIPLUSAT = 64
    CT_PLUS_CIAT_AI = 65
        
    otBASE = 66

    def is_detail(self):
        return self in _DETAIL_SURFACE_SHADER_TO_BASE_REMAP
    
    def strip_detail(self):
        if self.is_detail():
            return _DETAIL_SURFACE_SHADER_TO_BASE_REMAP[self]
        else:
            return self
      
class LightShader(Enum):
    FULLBRIGHT = 0
    FULLBRIGHT_CO = 1
    VLIGHT_BASIC = 2
    VLIGHT_BASIC_CO = 3
    VLIGHT_MASK_EMISSIVE = 4
    VLIGHT_MASK_EMISSIVE_CO = 5

class SpecularShader(Enum):
    VSPEC_BASIC = 0
    VSPEC_MASK = 1
    VSPEC_BASIC_CO = 2
    VSPEC_BASIC_MASK_CO = 3

class ToolShader(Enum):
    # 1 layer
	oBASE = 0
	cBASE = 1
	tBASE = 2
	obsBASE = 3
	beoBASE = 4
	etbsBASE = 5
	
    # 2 layers
	oBASE_LERP_tLAYER = 6
	cBASE_LERP_tLAYER = 7
	tBASE_LERP_tLAYER = 8
	
	oBASE_LERP_vLAYER = 9
	cBASE_LERP_vLAYER = 10
	oBASE_LERP_pLAYER = 11
	cBASE_LERP_pLAYER = 12
	
	oBASE_MOD_SHADOWMAP = 13
	cBASE_MOD_SHADOWMAP = 14

	oBASE_ADD_rbENV = 15
	etBASE_ADD_rbENV = 16

	oBASE_ADD_rbENV_MOD_SHADOWMAP = 17
	
	ADD_BASE = 18

	oBASE_ADD_rbSREFLECT = 19

	tBASE_vALPHA = 20
	LIQUID_ENV = 21
	LIQUID_LAYER_ENV = 22
	LIQUID_TEXTURE = 23
	LIQUID_MOLTEN_1LAYER = 24
	LIQUID_MOLTEN_2LAYER = 25

	oBASE_LERP_tLAYER_ADD_rbENV = 26
	oBASE_LERP_vLAYER_ADD_rbENV = 27
	oBASE_LERP_pLAYER_ADD_rbENV = 28

	pBASE = 29
	epbsBASE = 30
	ADD_vBASE = 31

_DETAIL_SURFACE_SHADER_TO_BASE_REMAP = {
    SurfaceShader.oBASE_DETAIL: SurfaceShader.oBASE,
    SurfaceShader.cBASE_DETAIL: SurfaceShader.cBASE,
    SurfaceShader.tBASE_DETAIL: SurfaceShader.tBASE,
    SurfaceShader.etBASE_DETAIL: SurfaceShader.etBASE,
    SurfaceShader.tBASE_ADD_SPEC_DETAIL: SurfaceShader.tBASE_ADD_SPEC,
    SurfaceShader.etBASE_ADD_SPEC_DETAIL: SurfaceShader.etBASE_ADD_SPEC,
    SurfaceShader.etBASE_ADD_bSPEC_DETAIL: SurfaceShader.etBASE_ADD_bSPEC,
    SurfaceShader.ADD_BASE_DETAIL: SurfaceShader.ADD_BASE,
    SurfaceShader.oBASE_LERP_tLAYER_DETAIL: SurfaceShader.oBASE_LERP_tLAYER,
    SurfaceShader.oBASE_LERP_vLAYER_DETAIL: SurfaceShader.oBASE_LERP_vLAYER,
    SurfaceShader.oBASE_LERP_pLAYER_DETAIL: SurfaceShader.oBASE_LERP_pLAYER,
    SurfaceShader.cBASE_LERP_tLAYER_DETAIL: SurfaceShader.cBASE_LERP_tLAYER,
    SurfaceShader.cBASE_LERP_vLAYER_DETAIL: SurfaceShader.cBASE_LERP_vLAYER,
    SurfaceShader.cBASE_LERP_pLAYER_DETAIL: SurfaceShader.cBASE_LERP_pLAYER,
    SurfaceShader.tBASE_LERP_tLAYER_DETAIL: SurfaceShader.tBASE_LERP_tLAYER,
    SurfaceShader.tBASE_ADD_SPEC_LERP_tLAYER_DETAIL: SurfaceShader.tBASE_ADD_SPEC_LERP_tLAYER,
    SurfaceShader.oBASE_ADD_rbENV_DETAIL: SurfaceShader.oBASE_ADD_rbENV,
    SurfaceShader.etBASE_ADD_rbENV_DETAIL: SurfaceShader.etBASE_ADD_rbENV,
    SurfaceShader.oBASE_LERP_tLAYER_ADD_rbENV_DETAIL: SurfaceShader.oBASE_LERP_tLAYER_ADD_rbENV,
    SurfaceShader.oBASE_LERP_vLAYER_ADD_rbENV_DETAIL: SurfaceShader.oBASE_LERP_vLAYER_ADD_rbENV,
    SurfaceShader.oBASE_LERP_pLAYER_ADD_rbENV_DETAIL: SurfaceShader.oBASE_LERP_pLAYER_ADD_rbENV,
}

_ENGINE_SHADER_TO_TOOL_SHADER_REMAP = {
    (SurfaceShader.oBASE, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE,
    (SurfaceShader.oBASE, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE,

    (SurfaceShader.cBASE, LightShader.VLIGHT_BASIC_CO, SpecularShader.VSPEC_BASIC_CO): ToolShader.cBASE,
    (SurfaceShader.cBASE, LightShader.VLIGHT_BASIC_CO, None): ToolShader.cBASE,

    (SurfaceShader.etBASE_ADD_SPEC, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.tBASE,
    (SurfaceShader.etBASE, LightShader.FULLBRIGHT, None): ToolShader.tBASE,
    (SurfaceShader.tBASE_ADD_SPEC, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.tBASE,
    (SurfaceShader.tBASE, LightShader.FULLBRIGHT, None): ToolShader.tBASE,

    (SurfaceShader.epBASE_ADD_SPEC, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.pBASE,
    (SurfaceShader.epBASE, LightShader.FULLBRIGHT, None): ToolShader.pBASE,
    (SurfaceShader.pBASE_ADD_SPEC, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.pBASE,
    (SurfaceShader.pBASE, LightShader.FULLBRIGHT, None): ToolShader.pBASE,

    (SurfaceShader.oBASE, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_MASK): ToolShader.obsBASE,

    (SurfaceShader.oBASE, LightShader.VLIGHT_MASK_EMISSIVE, SpecularShader.VSPEC_BASIC): ToolShader.beoBASE,
    (SurfaceShader.oBASE, LightShader.VLIGHT_MASK_EMISSIVE, None): ToolShader.beoBASE,

    (SurfaceShader.etBASE_ADD_bSPEC, LightShader.FULLBRIGHT, None): ToolShader.etbsBASE,

    (SurfaceShader.epBASE_ADD_bSPEC, LightShader.FULLBRIGHT, None): ToolShader.epbsBASE,

    (SurfaceShader.ADD_BASE, LightShader.FULLBRIGHT, None): ToolShader.ADD_BASE,

    (SurfaceShader.ADD_vBASE, LightShader.FULLBRIGHT, None): ToolShader.ADD_vBASE,

    (SurfaceShader.oBASE_LERP_pLAYER, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_pLAYER,
    (SurfaceShader.oBASE_LERP_pLAYER, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_pLAYER,

    (SurfaceShader.cBASE_LERP_pLAYER, LightShader.VLIGHT_BASIC_CO, None): ToolShader.cBASE_LERP_pLAYER,
    (SurfaceShader.cBASE_LERP_pLAYER, LightShader.VLIGHT_BASIC_CO, SpecularShader.VSPEC_BASIC_CO): ToolShader.cBASE_LERP_pLAYER,

    (SurfaceShader.oBASE_LERP_vLAYER, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_vLAYER,
    (SurfaceShader.oBASE_LERP_vLAYER, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_vLAYER,

    (SurfaceShader.cBASE_LERP_vLAYER, LightShader.VLIGHT_BASIC_CO, None): ToolShader.cBASE_LERP_vLAYER,
    (SurfaceShader.cBASE_LERP_vLAYER, LightShader.VLIGHT_BASIC_CO, SpecularShader.VSPEC_BASIC_CO): ToolShader.cBASE_LERP_vLAYER,

    (SurfaceShader.oBASE_LERP_tLAYER, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_tLAYER,
    (SurfaceShader.oBASE_LERP_tLAYER, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_tLAYER,

    (SurfaceShader.cBASE_LERP_tLAYER, LightShader.VLIGHT_BASIC_CO, None): ToolShader.cBASE_LERP_tLAYER,
    (SurfaceShader.cBASE_LERP_tLAYER, LightShader.VLIGHT_BASIC_CO, SpecularShader.VSPEC_BASIC_CO): ToolShader.cBASE_LERP_tLAYER,

    (SurfaceShader.tBASE_ADD_SPEC_LERP_tLAYER, LightShader.FULLBRIGHT, None): ToolShader.tBASE_LERP_tLAYER,
    (SurfaceShader.tBASE_ADD_SPEC_LERP_tLAYER, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.tBASE_LERP_tLAYER,

    (SurfaceShader.oBASE_ADD_rbENV, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_ADD_rbENV,
    (SurfaceShader.oBASE_ADD_rbENV, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_ADD_rbENV,

    (SurfaceShader.oBASE_LERP_tLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_tLAYER_ADD_rbENV,
    (SurfaceShader.oBASE_LERP_tLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_tLAYER_ADD_rbENV,

    (SurfaceShader.oBASE_LERP_vLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_vLAYER_ADD_rbENV,
    (SurfaceShader.oBASE_LERP_vLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_vLAYER_ADD_rbENV,

    (SurfaceShader.oBASE_LERP_pLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_LERP_pLAYER_ADD_rbENV,
    (SurfaceShader.oBASE_LERP_pLAYER_ADD_rbENV, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC): ToolShader.oBASE_LERP_pLAYER_ADD_rbENV,

    (SurfaceShader.etBASE_ADD_rbENV, LightShader.FULLBRIGHT, None): ToolShader.etBASE_ADD_rbENV,
    (SurfaceShader.etBASE_ADD_rbENV, LightShader.FULLBRIGHT, SpecularShader.VSPEC_BASIC_CO): ToolShader.etBASE_ADD_rbENV,

    (SurfaceShader.oBASE_ADD_rbSREFLECT, LightShader.VLIGHT_BASIC, None): ToolShader.oBASE_ADD_rbSREFLECT,
    (SurfaceShader.oBASE_ADD_rbSREFLECT, LightShader.VLIGHT_BASIC, SpecularShader.VSPEC_BASIC_CO): ToolShader.oBASE_ADD_rbSREFLECT,

    (SurfaceShader.LIQUID_ENV, LightShader.FULLBRIGHT, None): ToolShader.LIQUID_ENV,

    (SurfaceShader.LIQUID_LAYER_ENV, LightShader.FULLBRIGHT, None): ToolShader.LIQUID_LAYER_ENV,

    (SurfaceShader.LIQUID_TEXTURE, LightShader.FULLBRIGHT, None): ToolShader.LIQUID_TEXTURE,

    (SurfaceShader.LIQUID_MOLTEN_1LAYER, LightShader.FULLBRIGHT, None): ToolShader.LIQUID_MOLTEN_1LAYER,

    (SurfaceShader.LIQUID_MOLTEN_2LAYER, LightShader.FULLBRIGHT, None): ToolShader.LIQUID_MOLTEN_2LAYER,
}

class FLightShaderReg_t:
    def __init__(self, register_types: list[LightShaderRegisterType]):
        assert len(register_types) <= 16
        self.register_types = register_types

class FShaderReg_t:
    def __init__(self, tex_layer_count: int, uv_count: int, surface_type_flags: SurfaceShaderFlags, register_types: list[SurfaceShaderRegisterType]):
        assert len(register_types) <= 8
        self.tex_layer_count = tex_layer_count
        self.uv_count = uv_count
        self.surface_type_flags = surface_type_flags
        self.register_types = register_types
        
_LIGHT_SHADER_REGISTER_DATATYPES = {
    LightShaderRegisterType.BUMPMAP: FShTexInst_t,
    LightShaderRegisterType.ZMASK: FShTexInst_t,
    LightShaderRegisterType.EMASK: FShTexInst_t,
    LightShaderRegisterType.SMASK: FShTexInst_t,
    LightShaderRegisterType.LM_MOTIF: CFColorMotif,
    LightShaderRegisterType.DMOTIF: CFColorMotif,
    LightShaderRegisterType.EMOTIF: CFColorMotif,
    LightShaderRegisterType.SMOTIF: CFColorMotif,
    LightShaderRegisterType.BUMPMAP_TILE_FACTOR: float,
    LightShaderRegisterType.SEXP: float,
    LightShaderRegisterType.LMCOUNT: int,
    LightShaderRegisterType.LM: FShTexInst_t,
    LightShaderRegisterType.LM_TC: int #guess
}

_SHADER_REGISTER_DATATYPES = {
    SurfaceShaderRegisterType.LAYER0: FShTexInst_t,
    SurfaceShaderRegisterType.LAYER1: FShTexInst_t,
    SurfaceShaderRegisterType.LAYER2: FShTexInst_t,
    SurfaceShaderRegisterType.LAYER3: FShTexInst_t,
    SurfaceShaderRegisterType.DETAILMAP: FShTexInst_t,
    SurfaceShaderRegisterType.TC0: int,
    SurfaceShaderRegisterType.TC1: int,
    SurfaceShaderRegisterType.TC2: int,
    SurfaceShaderRegisterType.TC3: int,
    SurfaceShaderRegisterType.ENV_MOTIF: CFColorMotif,
    SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR: float
}

FShaders_aLightShaderRegs = [
    # FSHADERS_FULLBRIGHT
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ]),
    
    # FSHADERS_FULLBRIGHT_CO
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ]),
    
    # FSHADERS_VLIGHT_BASIC
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ]),
    
    # FSHADERS_VLIGHT_BASIC_CO
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ]),
    
    # FSHADERS_VLIGHT_MASK_EMISSIVE
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ]),
    
    # FSHADERS_VLIGHT_MASK_EMISSIVE_CO
    FLightShaderReg_t([
        LightShaderRegisterType.ZMASK,
        LightShaderRegisterType.EMASK,
        LightShaderRegisterType.SMASK,
        LightShaderRegisterType.BUMPMAP,
        LightShaderRegisterType.BUMPMAP_TILE_FACTOR,
        LightShaderRegisterType.DMOTIF,
        LightShaderRegisterType.EMOTIF,
        LightShaderRegisterType.SMOTIF,
        LightShaderRegisterType.SEXP,
        LightShaderRegisterType.LMCOUNT
    ])
]

FShaders_aShaderRegs = [
    # FSHADERS_oBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_cBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.CUTOUT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_tBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_etBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_tBASE_ADD_SPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_etBASE_ADD_SPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_etBASE_ADD_bSPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_ADD_BASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_oBASE_LERP_tLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_oBASE_LERP_vLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_oBASE_LERP_pLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_cBASE_LERP_tLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.CUTOUT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_cBASE_LERP_vLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.CUTOUT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_cBASE_LERP_pLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.CUTOUT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_tBASE_LERP_tLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_tBASE_ADD_SPEC_LERP_tLAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_oBASE_ADD_rbENV
    FShaderReg_t(2, 1, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_etBASE_ADD_rbENV
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_DETAIL
    FShaderReg_t(2, 1, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_cBASE_DETAIL,
    FShaderReg_t(2, 1, SurfaceShaderFlags.CUTOUT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_tBASE_DETAIL,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_etBASE_DETAIL,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_tBASE_ADD_SPEC_DETAIL,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_etBASE_ADD_SPEC_DETAIL,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_etBASE_ADD_bSPEC_DETAIL | SurfaceShaderFlags.DETAIL_MAP,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_ADD_BASE_DETAIL | SurfaceShaderFlags.DETAIL_MAP,
    FShaderReg_t(2, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_oBASE_LERP_tLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_oBASE_LERP_vLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_oBASE_LERP_pLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.CUTOUT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_cBASE_LERP_tLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.CUTOUT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    
    # FSHADERS_cBASE_LERP_vLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.CUTOUT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    # FSHADERS_cBASE_LERP_pLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.CUTOUT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    # FSHADERS_tBASE_LERP_tLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    # FSHADERS_tBASE_ADD_SPEC_LERP_tLAYER_DETAIL,
    FShaderReg_t(3, 2, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR
    ]),
    # FSHADERS_oBASE_ADD_rbENV_DETAIL,
    FShaderReg_t(3, 1, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),
    # FSHADERS_etBASE_ADD_rbENV_DETAIL,
    FShaderReg_t(3, 1, SurfaceShaderFlags.TRANSLUCENT | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_ADD_rbSREFLECT
    FShaderReg_t(2, 1, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_tBASE_vALPHA
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_LIQUID_ENV
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_LIQUID_LAYER_ENV
    FShaderReg_t(2, 2, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_LIQUID_TEXTURE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_LIQUID_MOLTEN_1LAYER
    FShaderReg_t(1, 1, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
    ]),

    # FSHADERS_LIQUID_MOLTEN_2LAYER
    FShaderReg_t(2, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1
    ]),

    # FSHADERS_oBASE_LERP_tLAYER_ADD_rbENV
    FShaderReg_t(3, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_LERP_vLAYER_ADD_rbENV
    FShaderReg_t(3, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_LERP_pLAYER_ADD_rbENV
    FShaderReg_t(3, 2, SurfaceShaderFlags.OPAQUE, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_LERP_tLAYER_ADD_rbENV_DETAIL
    FShaderReg_t(4, 2, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_LERP_vLAYER_ADD_rbENV_DETAIL
    FShaderReg_t(4, 2, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_oBASE_LERP_pLAYER_ADD_rbENV_DETAIL
    FShaderReg_t(4, 2, SurfaceShaderFlags.OPAQUE | SurfaceShaderFlags.DETAIL_MAP, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0,
        SurfaceShaderRegisterType.LAYER1,
        SurfaceShaderRegisterType.TC1,
        SurfaceShaderRegisterType.LAYER2,
        SurfaceShaderRegisterType.DETAILMAP,
        SurfaceShaderRegisterType.DETAILMAP_TILE_FACTOR,
        SurfaceShaderRegisterType.ENV_MOTIF
    ]),

    # FSHADERS_pBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_epBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_pBASE_ADD_SPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_epBASE_ADD_SPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_epBASE_ADD_bSPEC
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ]),

    # FSHADERS_ADD_vBASE
    FShaderReg_t(1, 1, SurfaceShaderFlags.TRANSLUCENT, [
        SurfaceShaderRegisterType.LAYER0,
        SurfaceShaderRegisterType.TC0
    ])
]

FDX8VB_InfoTable = [
    FDX8VB_Info(
        vtx_bytes=36,
        unlit=False,
        normal_count=1,
        weight_count=0,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=255,
        offset_norm=12,
        offset_color=24,
        offset_tc=28,
    ),
    FDX8VB_Info(
        vtx_bytes=44,
        unlit=False,
        normal_count=1,
        weight_count=0,
        color_count=1,
        tc_count=2,
        offset_pos=0,
        offset_weight=255,
        offset_norm=12,
        offset_color=24,
        offset_tc=28,
    ),
    FDX8VB_Info(
        vtx_bytes=48,
        unlit=False,
        normal_count=1,
        weight_count=3,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=12,
        offset_norm=24,
        offset_color=36,
        offset_tc=40,
    ),
    FDX8VB_Info(
        vtx_bytes=56,
        unlit=False,
        normal_count=1,
        weight_count=3,
        color_count=1,
        tc_count=2,
        offset_pos=0,
        offset_weight=12,
        offset_norm=24,
        offset_color=36,
        offset_tc=40,
    ),
    FDX8VB_Info(
        vtx_bytes=40,
        unlit=True,
        normal_count=0,
        weight_count=0,
        color_count=2,
        tc_count=2,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=16,
        offset_tc=24,
    ),
    FDX8VB_Info(
        vtx_bytes=16,
        unlit=False,
        normal_count=0,
        weight_count=0,
        color_count=1,
        tc_count=0,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=12,
        offset_tc=255,
    ),
    FDX8VB_Info(
        vtx_bytes=24,
        unlit=False,
        normal_count=0,
        weight_count=0,
        color_count=1,
        tc_count=1,
        offset_pos=0,
        offset_weight=255,
        offset_norm=255,
        offset_color=12,
        offset_tc=16,
    )
]

def get_surface_shader_reg_info(shader: SurfaceShader):
    id = shader.value
    if id >= 0 and id < len(FShaders_aShaderRegs):
        return FShaders_aShaderRegs[id]
    else:
        return None
      
def get_light_shader_reg_info(shader: LightShader):
    id = shader.value
    if id >= 0 and id < len(FShaders_aLightShaderRegs):
        return FShaders_aLightShaderRegs[id]
    else:
        return None

def get_shader_reg_datatype(register_type: LightShaderRegisterType | SurfaceShaderRegisterType):
    if isinstance(register_type, LightShaderRegisterType):
        return _LIGHT_SHADER_REGISTER_DATATYPES.get(register_type, None)
    else:
        return _SHADER_REGISTER_DATATYPES.get(register_type, None)
    
def get_tool_shader_from_shader_combination(surface_shader: SurfaceShader, light_shader: LightShader, specular_shader: SpecularShader):
    surface_shader = surface_shader.strip_detail()
    shader = _ENGINE_SHADER_TO_TOOL_SHADER_REMAP.get((surface_shader, light_shader, specular_shader), None)
    if shader is None:
        raise ValueError(f"No tool shader mapping found for combination: {surface_shader}, {light_shader}, {specular_shader}")
    return shader