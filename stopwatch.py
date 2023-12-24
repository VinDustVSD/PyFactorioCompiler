from datetime import datetime as dt
from random import randint


class Stopwatch:
    start_time: dt = None

    def __init__(self, text: str = "", new_line: bool = False):
        self.id = randint(100, 999)
        self.text = text
        self.new_line = new_line

    def start(self):
        print(f"[Stopwatch{self.id}] {self.text} ", end=None if self.new_line else "")
        self.start_time = dt.now()
        return self

    def stop(self):
        delta = dt.now() - self.start_time
        print(
            (f"[Stopwatch{self.id}] " if self.new_line else "") +
            f"completed in {delta if delta.total_seconds() >= 1 else str(delta.microseconds/1000) + 'ms'}")
