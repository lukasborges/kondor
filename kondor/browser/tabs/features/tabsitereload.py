from dataclasses import dataclass

from PySide6.QtCore import Property, QObject, Signal, Slot


@dataclass
class Change:
    extension_id: str
    extension_name: str
    was_enabled: bool
    is_enabled: bool


class TabSiteReload(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._changes: list[Change] = []

    def _is_pending(self) -> bool:
        return bool(self._changes)

    def _extension_name(self) -> str:
        return self._changes[-1].extension_name if self._changes else ""

    def _will_run(self) -> bool:
        return bool(self._changes) and self._changes[-1].is_enabled

    isPending = Property(bool, _is_pending, notify=changed)
    extensionName = Property(str, _extension_name, notify=changed)
    willRun = Property(bool, _will_run, notify=changed)

    def _index_of(self, extension_id: str) -> int:
        ids = [change.extension_id for change in self._changes]
        return ids.index(extension_id) if extension_id in ids else -1

    def _update(self, index: int, is_enabled: bool) -> None:
        change = self._changes.pop(index)
        change.is_enabled = is_enabled
        if change.is_enabled != change.was_enabled:
            self._changes.append(change)

    @Slot(str, str, bool)
    def recordToggle(self, extension_id: str, extension_name: str, is_enabled: bool) -> None:
        index = self._index_of(extension_id)
        if index < 0:
            self._changes.append(Change(extension_id, extension_name, not is_enabled, is_enabled))
        else:
            self._update(index, is_enabled)
        self.changed.emit()

    @Slot()
    def dismiss(self) -> None:
        if not self._changes:
            return
        self._changes.clear()
        self.changed.emit()
