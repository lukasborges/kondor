import time

from PySide6.QtCore import QObject, Signal, Slot

from kondor.browser.pointer.agentpointerpageapi import AgentPointerPageApi

REAL_INPUT_WINDOW_SECONDS = 0.1
PRESS = "pointerdown"


class AgentPointerBridge(QObject):
    agentMoved = Signal(float, float)
    agentPressed = Signal(float, float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._api = AgentPointerPageApi(self, self)
        self._last_real_input = float("-inf")

    @Slot(result=QObject)
    def pageApi(self) -> QObject:
        return self._api

    @Slot()
    def noteRealInput(self) -> None:
        self._last_real_input = time.monotonic()

    def is_real_input_recent(self) -> bool:
        return time.monotonic() - self._last_real_input < REAL_INPUT_WINDOW_SECONDS

    def receive_report(self, kind: str, x: float, y: float) -> None:
        if self.is_real_input_recent():
            return
        self.agentMoved.emit(x, y)
        if kind == PRESS:
            self.agentPressed.emit(x, y)
