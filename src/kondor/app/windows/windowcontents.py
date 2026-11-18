from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile


@dataclass
class WindowContents:
    is_private: bool = False
    urls: list[QUrl] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    agents: list[dict[str, object]] = field(default_factory=list)
    current_index: int = -1
    groups: list[dict[str, object]] = field(default_factory=list)
    tab_groups: list[int] = field(default_factory=list)
    profile: QQuickWebEngineProfile | None = None
    request: QObject | None = None


def initial_session_properties(contents: WindowContents) -> dict[str, object]:
    return {
        "initialUrls": contents.urls,
        "initialTitles": contents.titles,
        "initialAgents": contents.agents,
        "initialCurrentIndex": contents.current_index,
        "initialGroups": contents.groups,
        "initialTabGroups": contents.tab_groups,
    }


def initial_properties(contents: WindowContents) -> dict[str, object]:
    return {
        **initial_session_properties(contents),
        "privateWindow": contents.is_private,
        "initialProfile": contents.profile,
        "initialRequest": contents.request,
    }
