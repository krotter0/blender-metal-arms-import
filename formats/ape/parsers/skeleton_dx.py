
from .skeleton import SkeletonParser

class SkeletonParserDX(SkeletonParser):
    def _parse_platform_specific(self):
        bones = self._model.bones_dx
        return self._parse_bones(bones)