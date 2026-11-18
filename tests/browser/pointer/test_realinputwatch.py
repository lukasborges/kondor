import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QWindow
from PySide6.QtWidgets import QApplication

from kondor.browser.pointer.realinputclock import CLOCK
from kondor.browser.pointer.realinputwatch import RealInputWatch


@pytest.fixture
def window(qapp: object) -> QWindow:
    return QWindow()


@pytest.fixture
def watch(window: QWindow) -> RealInputWatch:
    CLOCK.forget()
    watching = RealInputWatch()
    watching.window = window
    return watching


def press(window: QWindow) -> None:
    point = QPointF(QPoint(5, 5))
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        point,
        point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, event)


def test_a_press_on_the_window_counts_as_real_input(watch: RealInputWatch, window: QWindow) -> None:
    watch.active = True
    press(window)
    assert CLOCK.consume_press()


def test_an_inactive_watch_ignores_input(watch: RealInputWatch, window: QWindow) -> None:
    press(window)
    assert not CLOCK.consume_press()


def test_a_deactivated_watch_stops_counting(watch: RealInputWatch, window: QWindow) -> None:
    watch.active = True
    watch.active = False
    press(window)
    assert not CLOCK.consume_press()
