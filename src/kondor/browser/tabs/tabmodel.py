from PySide6.QtCore import QModelIndex, QObject, QUrl, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodelclosing import TabModelClosing
from kondor.browser.tabs.tabmodelrows import NewTab
from kondor.browser.tabs.tabsleepscheduler import TabSleepScheduler


class TabModel(TabModelClosing):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sleep_scheduler = TabSleepScheduler(self)

    @Slot(result=Tab)
    @Slot(bool, result=Tab)
    @Slot(bool, QUrl, result=Tab)
    def addTab(self, is_private: bool = False, initial_url: QUrl | None = None) -> Tab | None:
        profiles = ProfileManager.instance()
        needs_private_profile = is_private or self._private_tabs
        if needs_private_profile and not profiles.is_private_browsing_available():
            return None
        profile = profiles.createPrivateProfile() if needs_private_profile else None
        profile = profile or profiles.defaultProfile()
        url = initial_url if initial_url is not None else QUrl()
        return self.insert_tab(NewTab(len(self._tabs), profile, url))

    def _child_tab_row(self) -> int:
        current = self._current_tab()
        if current is None:
            return len(self._tabs)
        return self._pinned_count() if current.pinned else self._current_index + 1

    @Slot(QQuickWebEngineProfile, QUrl, bool, result=Tab)
    def addTabWithProfile(
        self, profile: QQuickWebEngineProfile, url: QUrl, background: bool
    ) -> Tab:
        return self.insert_tab(NewTab(self._child_tab_row(), profile, url, not background))

    @Slot(Tab, result=int)
    def indexOfTab(self, tab: Tab) -> int:
        return self._tabs.index(tab) if tab in self._tabs else -1

    @Slot(int, int)
    def moveTab(self, source: int, target: int) -> None:
        if not self.is_valid_index(source) or not self.is_valid_index(target) or source == target:
            return
        current = self._current_tab()
        destination = target + 1 if target > source else target
        self.beginMoveRows(QModelIndex(), source, source, QModelIndex(), destination)
        self._tabs.insert(target, self._tabs.pop(source))
        self.endMoveRows()
        self.follow_current_tab(current)

    @Slot(int)
    def duplicateTab(self, index: int) -> None:
        if not self.is_valid_index(index):
            return
        source = self._tabs[index]
        copy = self.insert_tab(NewTab(index + 1, source.profile, source.url))
        if source.pinned:
            self.setPinned(self.indexOfTab(copy), True)

    @Slot(int, bool)
    def setPinned(self, index: int, pinned: bool) -> None:
        if not self.is_valid_index(index) or self._tabs[index].pinned == pinned:
            return
        self._tabs[index].set_pinned(pinned)
        target = self._pinned_count() - (1 if self._tabs[index].pinned else 0)
        if index != target:
            self.moveTab(index, target)
        self.pinnedCountChanged.emit()
