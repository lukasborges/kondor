from PySide6.QtCore import QElapsedTimer

MINIMUM_SAMPLE_MS = 1000
MILLISECONDS_PER_SECOND = 1000.0


class TransferSpeed:
    def __init__(self) -> None:
        self._timer = QElapsedTimer()
        self._last_received_bytes = 0
        self._bytes_per_second = 0.0

    def restart(self, received_bytes: int) -> None:
        self._bytes_per_second = 0.0
        self._last_received_bytes = received_bytes
        self._timer.restart()

    def update(self, received_bytes: int, elapsed_ms: int | None = None) -> None:
        elapsed = self._timer.elapsed() if elapsed_ms is None else elapsed_ms
        if elapsed < MINIMUM_SAMPLE_MS:
            return
        transferred = received_bytes - self._last_received_bytes
        self._bytes_per_second = transferred * MILLISECONDS_PER_SECOND / elapsed
        self._last_received_bytes = received_bytes
        self._timer.restart()

    def stop(self) -> None:
        self._bytes_per_second = 0.0

    def bytes_per_second(self) -> float:
        return self._bytes_per_second
