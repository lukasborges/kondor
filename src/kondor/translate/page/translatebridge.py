from PySide6.QtCore import Property, QObject, Signal, Slot
from shiboken6 import isValid

from kondor.browser.tabs.tab import Tab
from kondor.translate.page.translatepageapi import TranslatePageApi


class TranslateBridge(QObject):
    tabChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab: Tab | None = None
        self._api = TranslatePageApi(self, self)

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

    def receive_language(self, declared: str, sample: str) -> None:
        tab = self._get_tab()
        if tab is not None:
            tab.translation.receive_language(declared, sample)

    def receive_batch(self, batch_id: int, texts_json: str) -> None:
        tab = self._get_tab()
        if tab is not None:
            tab.translation.receive_batch(batch_id, texts_json)

    def receive_state(self, state: str) -> None:
        tab = self._get_tab()
        if tab is not None:
            tab.translation.receive_state(state)
