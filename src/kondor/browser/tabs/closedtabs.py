from dataclasses import dataclass, field

from PySide6.QtCore import QUrl


@dataclass
class ClosedTab:
    url: QUrl = field(default_factory=QUrl)
    title: str = ""
    index: int = 0


class ClosedTabs:
    MAX_CLOSED_TABS = 20

    def __init__(self) -> None:
        self._tabs: list[ClosedTab] = []

    def remember(self, url: QUrl, title: str, index: int) -> None:
        self._tabs.append(ClosedTab(url, title, index))
        del self._tabs[: -self.MAX_CLOSED_TABS]

    def take(self, index_from_newest: int) -> ClosedTab:
        return self._tabs.pop(len(self._tabs) - 1 - index_from_newest)

    def is_empty(self) -> bool:
        return not self._tabs

    def size(self) -> int:
        return len(self._tabs)

    def to_variant_list(self) -> list[dict[str, object]]:
        return [{"url": tab.url, "title": tab.title} for tab in reversed(self._tabs)]
