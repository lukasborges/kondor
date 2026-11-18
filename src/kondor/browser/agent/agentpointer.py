from typing import ClassVar

from PySide6.QtCore import QObject, Signal

from kondor.app.instance.sessionprotocol import PointerAction


class AgentPointer(QObject):
    _instance: ClassVar["AgentPointer | None"] = None

    moved = Signal(str, float, float)
    pressed = Signal(str, float, float)

    @classmethod
    def instance(cls) -> "AgentPointer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def announce(self, action: PointerAction) -> None:
        signal = self.pressed if action.kind == "press" else self.moved
        signal.emit(action.target_id, action.x, action.y)
