import time
from collections.abc import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify


class TabSleep(QObject):
    sleepingChanged = Signal()
    sleepRequested = Signal()
    idleSleepRequested = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__(parent)
        self._sleeping = False
        self._inactive_since: float | None = clock()

    sleeping = Property(bool, lambda self: self._sleeping, notify=sleepingChanged)

    @Slot(bool)
    def setSleeping(self, sleeping: bool) -> None:
        assign_and_notify((self, "_sleeping"), sleeping, self.sleepingChanged)

    @Slot()
    def putToSleep(self) -> None:
        self.sleepRequested.emit()

    @Slot()
    def requestIdleSleep(self) -> None:
        self.idleSleepRequested.emit()

    def mark_active(self) -> None:
        self._inactive_since = None

    def mark_inactive(self, now: float) -> None:
        self._inactive_since = now

    def inactive_seconds(self, now: float) -> float:
        if self._inactive_since is None:
            return 0.0
        return now - self._inactive_since
