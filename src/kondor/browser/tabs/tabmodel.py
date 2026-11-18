from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.groups.tabgroup import TabGroup
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

    @Slot(TabGroup, result=Tab)
    def newTabInGroup(self, group: TabGroup) -> Tab | None:
        tab: Tab | None = self.addTab(self._private_tabs)
        if tab is not None:
            self.addTabToGroup(self.indexOfTab(tab), group)
        return tab

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

    @Slot(QQuickWebEngineProfile, QObject, bool, result=Tab)
    def addTabForRequest(
        self, profile: QQuickWebEngineProfile, request: QObject, background: bool
    ) -> Tab:
        new_tab = NewTab(self._child_tab_row(), profile, activate=not background, request=request)
        return self.insert_tab(new_tab)

    @Slot(Tab, result=int)
    def indexOfTab(self, tab: Tab) -> int:
        return self._tabs.index(tab) if tab in self._tabs else -1

    @Slot(int, int)
    def moveTab(self, source: int, target: int) -> None:
        if not self.is_valid_index(source) or not self.is_valid_index(target) or source == target:
            return
        self.move_row_unless_there(source, self.clamp_move_target(source, target))

    @Slot(int, int, result=int)
    def clampedMoveTarget(self, source: int, target: int) -> int:
        if not self.is_valid_index(source):
            return target
        return self.clamp_move_target(source, target)

    @Slot(int, int)
    def stepTab(self, index: int, delta: int) -> None:
        self.moveTab(index, self.step_target(index, delta))

    @Slot(int)
    def duplicateTab(self, index: int) -> None:
        if not self.is_valid_index(index):
            return
        source = self._tabs[index]
        copy = self.insert_tab(NewTab(index + 1, source.profile, source.url))
        self.assign_group(copy, source.group)
        if source.pinned:
            self.setPinned(self.indexOfTab(copy), True)

    @Slot(int, bool)
    def setPinned(self, index: int, pinned: bool) -> None:
        if not self.is_valid_index(index) or self._tabs[index].pinned == pinned:
            return
        if pinned:
            self.leave_group(self._tabs[index])
        self._tabs[index].set_pinned(pinned)
        target = self._pinned_count() - (1 if self._tabs[index].pinned else 0)
        if index != target:
            self.moveTab(index, target)
        self.pinnedCountChanged.emit()
