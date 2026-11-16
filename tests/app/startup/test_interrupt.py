import signal
from collections.abc import Iterator

import pytest
from PySide6.QtCore import QCoreApplication, QObject

from kondor.app.startup import interrupt
from kondor.app.startup.interrupt import quit_on_interrupt


@pytest.fixture
def throwaway_parent() -> Iterator[QObject]:
    previous_handler = signal.getsignal(signal.SIGINT)
    parent = QObject()
    yield parent
    signal.signal(signal.SIGINT, previous_handler)
    parent.deleteLater()


def test_interrupt_signal_requests_quit(
    qapp: QCoreApplication,
    throwaway_parent: QObject,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quit_requests: list[bool] = []
    monkeypatch.setattr(QCoreApplication, "quit", lambda: quit_requests.append(True))
    quit_on_interrupt(throwaway_parent)
    assert signal.getsignal(signal.SIGINT) is interrupt.quit_application
    signal.raise_signal(signal.SIGINT)
    assert quit_requests == [True]
