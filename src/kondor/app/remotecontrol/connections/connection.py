from dataclasses import dataclass, field

from PySide6.QtCore import QDateTime
from PySide6.QtNetwork import QLocalSocket

AUTOMATION_TOOL_NAME = ""


@dataclass
class Connection:
    name: str
    since: QDateTime = field(default_factory=QDateTime.currentDateTime)
    socket: QLocalSocket | None = None
    ports: list[int] = field(default_factory=list)

    def is_session(self) -> bool:
        return self.socket is not None

    def kind(self) -> str:
        return "MCP session" if self.is_session() else "Automation tool"
