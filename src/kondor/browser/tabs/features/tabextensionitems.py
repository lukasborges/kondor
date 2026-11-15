from PySide6.QtCore import QObject, Signal, Slot


def key_of(extension_id: str, item_id: str) -> str:
    return f"{extension_id}/{item_id}"


class TabExtensionItems(QObject):
    changed = Signal()
    triggered = Signal(str, str, bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._checked: set[str] = set()

    @Slot(str, str, result=bool)
    def isChecked(self, extension_id: str, item_id: str) -> bool:
        return key_of(extension_id, item_id) in self._checked

    @Slot(str, str, bool)
    def setChecked(self, extension_id: str, item_id: str, checked: bool) -> None:
        if self.isChecked(extension_id, item_id) == checked:
            return
        self._update(key_of(extension_id, item_id), checked)
        self.changed.emit()

    def _update(self, key: str, checked: bool) -> None:
        if checked:
            self._checked.add(key)
        else:
            self._checked.discard(key)

    @Slot(str, str, bool)
    def trigger(self, extension_id: str, item_id: str, checkable: bool) -> None:
        checked = checkable and not self.isChecked(extension_id, item_id)
        if checkable:
            self.setChecked(extension_id, item_id, checked)
        self.triggered.emit(extension_id, item_id, checked)
