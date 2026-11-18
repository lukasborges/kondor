from PySide6.QtCore import QObject, Signal, Slot

from kondor.browser.pointer.agentpointerpageapi import AgentPointerPageApi
from kondor.browser.pointer.realinputclock import CLOCK

PRESS = "pointerdown"


class AgentPointerBridge(QObject):
    agentMoved = Signal(float, float)
    agentPressed = Signal(float, float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._api = AgentPointerPageApi(self, self)

    @Slot(result=QObject)
    def pageApi(self) -> QObject:
        return self._api

    def receive_report(self, kind: str, x: float, y: float) -> None:
        if CLOCK.is_recent():
            return
        self.agentMoved.emit(x, y)
        if kind == PRESS:
            self.agentPressed.emit(x, y)
