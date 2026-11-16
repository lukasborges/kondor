import signal

from PySide6.QtCore import QCoreApplication, QTimer

from kondor.app.startup.interrupt import quit_on_interrupt


def test_interrupt_signal_quits_the_event_loop(qapp: QCoreApplication) -> None:
    quit_on_interrupt(qapp)
    QTimer.singleShot(300, lambda: signal.raise_signal(signal.SIGINT))
    QTimer.singleShot(5000, lambda: qapp.exit(1))
    assert qapp.exec() == 0
