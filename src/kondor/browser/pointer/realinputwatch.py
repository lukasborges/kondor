from PySide6.QtCore import Property, QEvent, QObject, Signal

from kondor.browser.pointer.realinputclock import CLOCK

REAL_INPUT_EVENTS = frozenset(
    {
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseMove,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.TouchUpdate,
    }
)


class RealInputWatch(QObject):
    windowChanged = Signal()
    activeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window: QObject | None = None
        self._active = False
        self._watched: QObject | None = None

    def _get_window(self) -> QObject | None:
        return self._window

    def _set_window(self, window: QObject | None) -> None:
        if window is self._window:
            return
        self._window = window
        self.windowChanged.emit()
        self._refresh()

    def _get_active(self) -> bool:
        return self._active

    def _set_active(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        self.activeChanged.emit()
        self._refresh()

    window = Property(QObject, _get_window, _set_window, notify=windowChanged)
    active = Property(bool, _get_active, _set_active, notify=activeChanged)

    def _refresh(self) -> None:
        self._stop_watching()
        if self._active and self._window is not None:
            self._window.installEventFilter(self)
            self._watched = self._window

    def _stop_watching(self) -> None:
        if self._watched is not None:
            self._watched.removeEventFilter(self)
        self._watched = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() in REAL_INPUT_EVENTS:
            CLOCK.note()
        return False
