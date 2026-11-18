from collections.abc import Iterable
from dataclasses import dataclass

from PySide6.QtCore import QMetaObject, QModelIndex, QObject, QUrl

from kondor.app.windows.tabsearchtext import (
    address_without_scheme,
    highlight,
    matches_all_words,
    query_words,
)
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE


@dataclass(frozen=True)
class SearchableTab:
    tab: QObject
    window_number: int
    is_current: bool

    @property
    def title(self) -> str:
        return str(self.tab.property("title") or "")

    @property
    def address(self) -> str:
        url = self.tab.property("url")
        return address_without_scheme(url) if isinstance(url, QUrl) else ""

    @property
    def is_sleeping(self) -> bool:
        sleep = self.tab.property("sleep")
        return sleep is not None and sleep.property("sleeping") is True


def is_private(window: QObject) -> bool:
    return window.property("privateWindow") is True


def window_tabs(window: QObject) -> list[QObject]:
    model = window.findChild(TabModel)
    if model is None:
        return []
    return [
        model.data(model.index(row, 0, QModelIndex()), TAB_ROLE) for row in range(model.rowCount())
    ]


def current_tab_of(window: QObject) -> QObject | None:
    model = window.findChild(TabModel)
    return model.property("currentTab") if model is not None else None


def searched_windows(windows: Iterable[QObject], current: QObject) -> list[tuple[QObject, int]]:
    if is_private(current):
        return [(current, 1)]
    others = [w for w in windows if w is not current and not is_private(w)]
    numbered = [(w, number) for number, w in enumerate(others, start=2)]
    return [(current, 1), *numbered]


def all_tabs(windows: Iterable[QObject], current: QObject) -> list[SearchableTab]:
    result: list[SearchableTab] = []
    for window, number in searched_windows(windows, current):
        selected = current_tab_of(window)
        result += [
            SearchableTab(tab, number, window is current and tab is selected)
            for tab in window_tabs(window)
            if tab is not None
        ]
    return result


def describe(entry: SearchableTab, words: list[str]) -> dict[str, object]:
    return {
        "tab": entry.tab,
        "windowNumber": entry.window_number,
        "titleHtml": highlight(entry.title or entry.address, words),
        "addressHtml": highlight(entry.address, words),
        "pageUrl": entry.tab.property("url"),
        "isCurrent": entry.is_current,
        "isSleeping": entry.is_sleeping,
    }


def search(windows: Iterable[QObject], current: QObject, query: str) -> list[dict[str, object]]:
    words = query_words(query)
    found = [
        entry
        for entry in all_tabs(windows, current)
        if matches_all_words(f"{entry.title} {entry.address}", words)
    ]
    return [describe(entry, words) for entry in found]


def close_tab(windows: Iterable[QObject], tab: QObject) -> None:
    for window in windows:
        model = window.findChild(TabModel)
        if model is not None and model.indexOfTab(tab) >= 0:
            close_in(window, model, tab)
            return


def close_in(window: QObject, model: TabModel, tab: QObject) -> None:
    if model.rowCount() <= 1:
        QMetaObject.invokeMethod(window, "close")
    else:
        model.closeTabObject(tab)
