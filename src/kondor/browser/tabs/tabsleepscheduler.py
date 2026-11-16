import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QObject, QTimer

from kondor.browser.tabs.tab import Tab
from kondor.core.settings.settings import Settings

if TYPE_CHECKING:
    from kondor.browser.tabs.tabmodelrows import TabModelRows

CHECK_INTERVAL_MILLISECONDS = 60_000


def is_exempt_from_sleep(tab: Tab) -> bool:
    exemptions = (tab.pinned, tab.newTabPage, tab.crashed, tab.readerActive, tab.devToolsOpen)
    return any(exemptions)


def may_sleep(tab: Tab, now: float, settings: Settings) -> bool:
    if not settings.tabSleepEnabled or tab.sleep.sleeping or is_exempt_from_sleep(tab):
        return False
    return bool(tab.sleep.inactive_seconds(now) >= settings.tabSleepMinutes * 60)


class TabSleepScheduler(QObject):
    def __init__(
        self,
        model: "TabModelRows",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__(model)
        self._model = model
        self._clock = clock
        self._previous: Tab | None = None
        model.currentTabChanged.connect(self._on_current_tab_changed)
        model.rowsInserted.connect(self._on_rows_inserted)
        self._timer = QTimer(self)
        self._timer.setInterval(CHECK_INTERVAL_MILLISECONDS)
        self._timer.timeout.connect(self.check)
        self._timer.start()

    def _on_current_tab_changed(self) -> None:
        current = self._model.currentTab
        if self._previous is not current and self._previous in self._model.all_tabs():
            self._previous.sleep.mark_inactive(self._clock())
        if current is not None:
            current.sleep.mark_active()
        self._previous = current

    def _on_rows_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        for tab in self._model.all_tabs()[first : last + 1]:
            tab.sleep.mark_inactive(self._clock())

    def check(self) -> None:
        now = self._clock()
        settings = Settings.instance()
        for tab in self._model.all_tabs():
            if tab is not self._model.currentTab and may_sleep(tab, now, settings):
                tab.sleep.requestIdleSleep()
