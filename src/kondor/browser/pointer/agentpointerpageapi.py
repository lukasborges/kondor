from typing import Protocol

from PySide6.QtCore import QObject, Slot


class PointerReportOwner(Protocol):
    def receive_report(self, kind: str, x: float, y: float) -> None: ...


class AgentPointerPageApi(QObject):
    def __init__(self, bridge: QObject, owner: PointerReportOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot(str, float, float)
    def report(self, kind: str, x: float, y: float) -> None:
        self._owner.receive_report(kind, x, y)
