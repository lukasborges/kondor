from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile


@dataclass
class WindowContents:
    is_private: bool = False
    urls: list[QUrl] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    current_index: int = -1
    profile: QQuickWebEngineProfile | None = None
    request: QObject | None = None


def initial_properties(contents: WindowContents) -> dict[str, object]:
    return {
        "privateWindow": contents.is_private,
        "initialUrls": contents.urls,
        "initialTitles": contents.titles,
        "initialCurrentIndex": contents.current_index,
        "initialProfile": contents.profile,
        "initialRequest": contents.request,
    }
