from dataclasses import dataclass
from typing import Self

@dataclass
class ParsedBone:
    index: int
    name: str
    parent_index: int
    bone_to_model_matrix: tuple[tuple[float, float, float, float]]
    parent_bone: Self = None
    children: list[Self] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class ParsedSkeleton:
    root_bones: list[ParsedBone] = None
    bones: list[ParsedBone] = None

    def __post_init__(self):
        if self.root_bones is None:
            self.root_bones = []
        if self.bones is None:
            self.bones = []