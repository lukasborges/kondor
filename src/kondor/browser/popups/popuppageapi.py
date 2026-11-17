from typing import Protocol

from PySide6.QtCore import QObject, Slot


class BlockedReportOwner(Protocol):
    def receive_blocked(self, url: str) -> None: ...


class PopupPageApi(QObject):
    def __init__(self, bridge: QObject, owner: BlockedReportOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot(str)
    def reportBlocked(self, url: str) -> None:
        self._owner.receive_blocked(url)
