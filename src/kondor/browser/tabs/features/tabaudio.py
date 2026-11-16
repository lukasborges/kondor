from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify


class TabAudio(QObject):
    audibleChanged = Signal()
    mutedChanged = Signal()
    mutedToggleRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audible = False
        self._muted = False

    isAudible = Property(bool, lambda self: self._audible, notify=audibleChanged)
    isMuted = Property(bool, lambda self: self._muted, notify=mutedChanged)

    @Slot(bool)
    def setAudible(self, audible: bool) -> None:
        assign_and_notify((self, "_audible"), audible, self.audibleChanged)

    @Slot(bool)
    def setMuted(self, muted: bool) -> None:
        assign_and_notify((self, "_muted"), muted, self.mutedChanged)

    @Slot()
    def toggleMuted(self) -> None:
        self.mutedToggleRequested.emit()
