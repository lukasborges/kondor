import signal
from types import FrameType

from PySide6.QtCore import QCoreApplication, QObject, QTimer

POLL_INTERVAL_MS = 200


def quit_application(signal_number: int, frame: FrameType | None) -> None:
    QCoreApplication.quit()


def do_nothing() -> None:
    return


def quit_on_interrupt(parent: QObject) -> None:
    signal.signal(signal.SIGINT, quit_application)
    timer = QTimer(parent)
    timer.timeout.connect(do_nothing)
    timer.start(POLL_INTERVAL_MS)
