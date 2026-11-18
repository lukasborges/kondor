import time
from collections import deque

PRESS_PAIRING_SECONDS = 2.0
MOVE_QUIET_SECONDS = 1.0


class RealInputClock:
    def __init__(self) -> None:
        self._presses: deque[float] = deque()
        self._last_activity = float("-inf")

    def forget(self) -> None:
        self._presses.clear()
        self._last_activity = float("-inf")

    def note_activity(self) -> None:
        self._last_activity = time.monotonic()

    def note_press(self) -> None:
        self.note_activity()
        self._presses.append(self._last_activity)

    def consume_press(self) -> bool:
        self._drop_stale_presses()
        if not self._presses:
            return False
        self._presses.popleft()
        return True

    def is_moving(self) -> bool:
        return time.monotonic() - self._last_activity < MOVE_QUIET_SECONDS

    def _drop_stale_presses(self) -> None:
        oldest_allowed = time.monotonic() - PRESS_PAIRING_SECONDS
        while self._presses and self._presses[0] < oldest_allowed:
            self._presses.popleft()


CLOCK = RealInputClock()
