from PySide6.QtCore import Property, QObject, Signal, Slot
from shiboken6 import isValid

from kondor.browser.popups.popuppageapi import PopupPageApi
from kondor.browser.popups.popupurl import parse_blocked_url
from kondor.browser.tabs.tab import Tab


class PopupBridge(QObject):
    tabChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab: Tab | None = None
        self._api = PopupPageApi(self, self)

    def _get_tab(self) -> Tab | None:
        return self._tab if self._tab is not None and isValid(self._tab) else None

    def _set_tab(self, tab: Tab | None) -> None:
        if self._get_tab() is tab:
            return
        self._tab = tab
        self.tabChanged.emit()

    tab = Property(Tab, _get_tab, _set_tab, notify=tabChanged)

    @Slot(result=QObject)
    def pageApi(self) -> QObject:
        return self._api

    def receive_blocked(self, url: str) -> None:
        tab = self._get_tab()
        parsed = parse_blocked_url(url)
        if tab is not None and parsed is not None:
            tab.popups.add_blocked(parsed)
