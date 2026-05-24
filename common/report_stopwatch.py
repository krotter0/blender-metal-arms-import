import os
import bpy
from .stopwatch import Stopwatch

class ReportStopwatch(Stopwatch):
    def __init__(self, filepath: str, operator: bpy.types.Operator):
        super().__init__()
        self.filename = os.path.basename(filepath)
        self.operator = operator

    def report(self):
        self.stop()
        self.operator.report({'INFO'}, f"Finished importing {self.filename} in {self}")