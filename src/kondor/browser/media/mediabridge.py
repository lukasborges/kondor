from PySide6.QtCore import Property, QObject, Signal, Slot
from shiboken6 import isValid

from kondor.browser.media.mediapageapi import MediaPageApi
from kondor.browser.media.mediastate import parse_report
from kondor.browser.tabs.tab import Tab


class MediaBridge(QObject):
    tabChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab: Tab | None = None
        self._api = MediaPageApi(self, self)

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

    @Slot(str, float)
    def perform(self, action: str, seconds: float) -> None:
        self._api.actionRequested.emit(action, seconds)

    def receive_report(self, report: dict[str, object]) -> None:
        tab = self._get_tab()
        if tab is not None:
            tab.media.apply(parse_report(report))
