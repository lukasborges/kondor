from dataclasses import dataclass, field

from PySide6.QtCore import QUrl


@dataclass
class SessionTab:
    url: QUrl = field(default_factory=QUrl)
    title: str = ""


@dataclass
class SessionWindow:
    tabs: list[SessionTab] = field(default_factory=list)
    current_index: int = 0
