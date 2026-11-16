from collections.abc import Iterable
from dataclasses import dataclass

from PySide6.QtCore import QModelIndex, QObject, QUrl

from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE


@dataclass(frozen=True)
class OpenTab:
    window: QObject
    tab_model: QObject
    tab: QObject

    @property
    def title(self) -> str:
        return str(self.tab.property("title") or "")

    @property
    def url(self) -> QUrl:
        url = self.tab.property("url")
        return url if isinstance(url, QUrl) else QUrl()


def is_shown_in_runner(tab: QObject | None) -> bool:
    if tab is None or tab.property("isPrivate") or tab.property("newTabPage"):
        return False
    url = tab.property("url")
    return isinstance(url, QUrl) and not url.isEmpty()


def tabs_of_window(window: QObject) -> list[OpenTab]:
    model = window.findChild(TabModel)
    rows = range(model.rowCount()) if model is not None else range(0)
    tabs = [model.data(model.index(row, 0, QModelIndex()), TAB_ROLE) for row in rows]
    return [OpenTab(window, model, tab) for tab in tabs if is_shown_in_runner(tab)]


def open_tabs(windows: Iterable[QObject]) -> list[OpenTab]:
    normal_windows = [window for window in windows if window.property("privateWindow") is not True]
    return [tab for window in normal_windows for tab in tabs_of_window(window)]
