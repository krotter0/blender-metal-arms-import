
from .skeleton import SkeletonParser

class SkeletonParserGC(SkeletonParser):
    def _parse_platform_specific(self):
        bones = self._model.bones_gc
        return self._parse_bones(bones)