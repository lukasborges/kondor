from PySide6.QtCore import Property, QObject, QRectF, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify


class TabPasswordSuggestion(QObject):
    fieldChanged = Signal()
    generateRequested = Signal()
    generatedPasswordSaved = Signal()

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._kind = ""
        self._is_offered = False
        self._rect = QRectF()
        self._generated: tuple[str, str] | None = None

    fieldKind = Property(str, lambda self: self._kind, notify=fieldChanged)
    isOffered = Property(bool, lambda self: self._is_offered, notify=fieldChanged)
    fieldRect = Property(QRectF, lambda self: self._rect, notify=fieldChanged)

    def show_field(self, kind: str, offer: bool, rect: QRectF) -> None:
        if self._is_private:
            return
        self._kind, self._is_offered, self._rect = kind, offer, rect
        self.fieldChanged.emit()

    def clear_field(self) -> None:
        if self._is_private or not self._kind:
            return
        self._kind, self._is_offered, self._rect = "", False, QRectF()
        self.fieldChanged.emit()

    def remember_generated(self, origin: str, password: str) -> None:
        if not self._is_private:
            self._generated = (origin, password)

    def take_generated(self, origin: str, password: str) -> bool:
        matches = self._generated == (origin, password)
        if matches:
            self._generated = None
        return matches

    def announce_saved(self) -> None:
        self.generatedPasswordSaved.emit()

    @Slot()
    def generate(self) -> None:
        if self._is_private:
            return
        assign_and_notify((self, "_is_offered"), False, self.fieldChanged)
        self.generateRequested.emit()

    @Slot()
    def dismiss(self) -> None:
        assign_and_notify((self, "_is_offered"), False, self.fieldChanged)
