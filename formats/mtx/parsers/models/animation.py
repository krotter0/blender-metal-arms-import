from dataclasses import dataclass

from ...types.anim import AnimFlags

@dataclass
class ParsedAnimationBone:
    translation_key_data: list[tuple[float, float, float]]
    orientation_key_data: list[tuple[float, float, float, float]]
    scale_key_data: list[float]

    translation_key_times: list[float]
    orientation_key_times: list[float]
    scale_key_times: list[float]

@dataclass
class ParsedAnimation:
    flags: AnimFlags
    total_seconds: float
    bones: dict[str, ParsedAnimationBone]