from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot


class ReportOwner(Protocol):
    def receive_report(self, report: dict[str, object]) -> None: ...


class MediaPageApi(QObject):
    actionRequested = Signal(str, float)

    def __init__(self, bridge: QObject, owner: ReportOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot("QVariantMap")
    def report(self, state: dict[str, object]) -> None:
        self._owner.receive_report(state)
