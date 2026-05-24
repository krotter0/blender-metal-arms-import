import time

class Stopwatch:
    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __str__(self):
        return f"{(self.elapsed_time * 1000):.3f} ms"