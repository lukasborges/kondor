from dataclasses import dataclass, field

from PySide6.QtCore import QUrl

NO_GROUP = -1


@dataclass
class SessionGroup:
    name: str = ""
    color: str = "blue"
    collapsed: bool = False


@dataclass
class SessionTab:
    url: QUrl = field(default_factory=QUrl)
    title: str = ""
    has_agent_access: bool = False
    agent_name: str = ""
    group: int = NO_GROUP


@dataclass
class SessionWindow:
    tabs: list[SessionTab] = field(default_factory=list)
    current_index: int = 0
    groups: list[SessionGroup] = field(default_factory=list)
