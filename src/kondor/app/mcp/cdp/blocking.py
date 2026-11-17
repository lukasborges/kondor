import time
from collections.abc import Callable

from PySide6.QtCore import QEventLoop, QTimer

POLL_MILLISECONDS = 5


def wait_until(condition: Callable[[], bool], timeout_milliseconds: int) -> bool:
    deadline = time.monotonic() + timeout_milliseconds / 1000
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(POLL_MILLISECONDS)
    timer.timeout.connect(lambda: stop_when_done(loop, condition, deadline))
    timer.start()
    loop.exec()
    return condition()


def stop_when_done(loop: QEventLoop, condition: Callable[[], bool], deadline: float) -> None:
    if condition() or time.monotonic() >= deadline:
        loop.quit()
