import time

REAL_INPUT_WINDOW_SECONDS = 0.1


class RealInputClock:
    def __init__(self) -> None:
        self.last_input = float("-inf")

    def forget(self) -> None:
        self.last_input = float("-inf")

    def note(self) -> None:
        self.last_input = time.monotonic()

    def is_recent(self) -> bool:
        return time.monotonic() - self.last_input < REAL_INPUT_WINDOW_SECONDS


CLOCK = RealInputClock()
