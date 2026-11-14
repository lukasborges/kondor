from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtWebEngineCore import QWebEnginePermission


def resolve(permission: QWebEnginePermission, grant: bool) -> None:
    if grant:
        permission.grant()
    else:
        permission.deny()


class TabPermissions(QObject):
    pendingChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._queue: list[QWebEnginePermission] = []

    def _pending(self) -> QWebEnginePermission | None:
        return self._queue[0] if self._queue else None

    pending = Property("QVariant", _pending, notify=pendingChanged)

    @Slot(QWebEnginePermission)
    def enqueue(self, permission: QWebEnginePermission) -> None:
        if not permission.isValid():
            return
        was_empty = not self._queue
        self._queue.append(permission)
        if was_empty:
            self.pendingChanged.emit()

    def _drop_invalid_front(self) -> bool:
        dropped = False
        while self._queue and not self._queue[0].isValid():
            self._queue.pop(0)
            dropped = True
        return dropped

    @Slot(bool)
    def answer(self, grant: bool) -> None:
        dropped = self._drop_invalid_front()
        has_question = bool(self._queue)
        if has_question:
            resolve(self._queue.pop(0), grant)
        if dropped or has_question:
            self.pendingChanged.emit()

    def deny_all(self) -> None:
        if not self._queue:
            return
        for permission in self._queue:
            if permission.isValid():
                permission.deny()
        self._queue.clear()
        self.pendingChanged.emit()
