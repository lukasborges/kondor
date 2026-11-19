from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.closedtabs import ClosedTab, ClosedTabs
from kondor.browser.tabs.groups.tabmodelgroupcommands import TabModelGroupCommands
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodelrows import NewTab


class TabModelClosing(TabModelGroupCommands):
    canReopenClosedTabChanged = Signal()
    recentlyClosedChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._closed = ClosedTabs()

    def _can_reopen_closed_tab(self) -> bool:
        return not self._closed.is_empty()

    def _recently_closed(self) -> list[dict[str, object]]:
        return self._closed.to_variant_list()

    canReopenClosedTab = Property(bool, _can_reopen_closed_tab, notify=canReopenClosedTabChanged)
    recentlyClosed = Property("QVariantList", _recently_closed, notify=recentlyClosedChanged)

    def remember_closed(self, index: int) -> None:
        closing = self._tabs[index]
        if closing.isPrivate or closing.newTabPage:
            return
        was_empty = self._closed.is_empty()
        self._closed.remember(closing.url, closing.title, index)
        if was_empty:
            self.canReopenClosedTabChanged.emit()
        self.recentlyClosedChanged.emit()

    @Slot(int)
    def closeTab(self, index: int) -> None:
        if not self.is_valid_index(index):
            return
        self.remember_closed(index)
        tab = self.remove_row(index)
        self.fix_current_after_removal(index)
        tab.deleteLater()

    @Slot(Tab)
    def closeTabObject(self, tab: Tab) -> None:
        if tab in self._tabs:
            self.closeTab(self._tabs.index(tab))

    @Slot()
    @Slot(int)
    def reopenClosedTab(self, index: int = 0) -> None:
        if index < 0 or index >= self._closed.size():
            return
        self._restore(self._closed.take(index))
        if self._closed.is_empty():
            self.canReopenClosedTabChanged.emit()
        self.recentlyClosedChanged.emit()

    def _restore(self, closed: ClosedTab) -> None:
        row = max(self._pinned_count(), min(closed.index, len(self._tabs)))
        profile = ProfileManager.instance().defaultProfile()
        tab = self.insert_tab(NewTab(row, profile, closed.url))
        if closed.title:
            tab.setTitle(closed.title)

    @Slot(int)
    def closeOtherTabs(self, index: int) -> None:
        if not self.is_valid_index(index):
            return
        kept = self._tabs[index]
        for tab in reversed(list(self._tabs)):
            if tab is not kept and not tab.pinned:
                self.closeTabObject(tab)

    @Slot(int)
    def closeTabsToTheRight(self, index: int) -> None:
        if not self.is_valid_index(index):
            return
        for row in range(len(self._tabs) - 1, index, -1):
            if not self._tabs[row].pinned:
                self.closeTab(row)
