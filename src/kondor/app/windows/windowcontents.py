from dataclasses import dataclass, field

from PySide6.QtCore import QUrl


@dataclass
class WindowContents:
    is_private: bool = False
    urls: list[QUrl] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    current_index: int = -1


def initial_properties(contents: WindowContents) -> dict[str, object]:
    return {
        "privateWindow": contents.is_private,
        "initialUrls": contents.urls,
        "initialTitles": contents.titles,
        "initialCurrentIndex": contents.current_index,
    }
