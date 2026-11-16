from dataclasses import dataclass, field

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab

TAB_ROLE = Qt.ItemDataRole.UserRole + 1


@dataclass
class NewTab:
    index: int
    profile: QQuickWebEngineProfile | None
    url: QUrl = field(default_factory=QUrl)
    activate: bool = True
    request: QObject | None = None


class TabModelRows(QAbstractListModel):
    countChanged = Signal()
    currentIndexChanged = Signal()
    currentTabChanged = Signal()
    pinnedCountChanged = Signal()
    privateTabsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tabs: list[Tab] = []
        self._current_index = -1
        self._private_tabs = False

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return 0 if parent is not None and parent.isValid() else len(self._tabs)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Tab | None:
        if not index.isValid() or not self.is_valid_index(index.row()) or role != TAB_ROLE:
            return None
        tab: Tab = self._tabs[index.row()]
        return tab

    def roleNames(self) -> dict[int, QByteArray]:
        return {TAB_ROLE: QByteArray(b"tab")}

    def is_valid_index(self, index: int) -> bool:
        return 0 <= index < len(self._tabs)

    def _current_tab(self) -> Tab | None:
        if not self.is_valid_index(self._current_index):
            return None
        return self._tabs[self._current_index]

    def all_tabs(self) -> list[Tab]:
        return list(self._tabs)

    def _pinned_count(self) -> int:
        return sum(1 for tab in self._tabs if tab.pinned)

    count = Property(int, lambda self: len(self._tabs), notify=countChanged)
    currentIndex = Property(int, lambda self: self._current_index, notify=currentIndexChanged)
    currentTab = Property(Tab, _current_tab, notify=currentTabChanged)
    pinnedCount = Property(int, _pinned_count, notify=pinnedCountChanged)

    def _private_tabs_enabled(self) -> bool:
        return self._private_tabs

    def _set_private_tabs(self, private_tabs: bool) -> None:
        if self._private_tabs == private_tabs:
            return
        self._private_tabs = private_tabs
        self.privateTabsChanged.emit()

    privateTabs = Property(
        bool, _private_tabs_enabled, _set_private_tabs, notify=privateTabsChanged
    )

    @Slot(int)
    def setCurrentIndex(self, index: int) -> None:
        if not self.is_valid_index(index) or index == self._current_index:
            return
        self._current_index = index
        self.notify_current_changed()

    def notify_current_changed(self) -> None:
        self.currentIndexChanged.emit()
        self.currentTabChanged.emit()

    def profile_for(self, requested: QQuickWebEngineProfile | None) -> QQuickWebEngineProfile:
        profiles = ProfileManager.instance()
        profile = requested if requested is not None else profiles.defaultProfile()
        if self._private_tabs and not profile.isOffTheRecord():
            return profiles.createPrivateProfile()
        return profile

    def insert_row(self, index: int, tab: Tab) -> None:
        self.beginInsertRows(QModelIndex(), index, index)
        self._tabs.insert(index, tab)
        self.endInsertRows()
        self.countChanged.emit()
        self.pinnedCountChanged.emit()

    def insert_tab(self, new_tab: NewTab) -> Tab:
        tab = Tab(self.profile_for(new_tab.profile), self)
        tab.setUrl(new_tab.url)
        tab.adopt_request(new_tab.request)
        index = max(0, min(new_tab.index, len(self._tabs)))
        self.insert_row(index, tab)
        self.keep_current_when_inserted_before(index)
        if new_tab.activate:
            self.setCurrentIndex(index)
        return tab

    def keep_current_when_inserted_before(self, index: int) -> None:
        if self._current_index < index:
            return
        self._current_index += 1
        self.notify_current_changed()

    def remove_row(self, index: int) -> Tab:
        self.beginRemoveRows(QModelIndex(), index, index)
        tab = self._tabs.pop(index)
        self.endRemoveRows()
        self.countChanged.emit()
        self.pinnedCountChanged.emit()
        return tab

    def fix_current_after_removal(self, removed_index: int) -> None:
        if self._current_index > removed_index:
            self._current_index -= 1
        elif self._current_index == removed_index:
            self._current_index = min(removed_index, len(self._tabs) - 1) if self._tabs else -1
        else:
            return
        self.notify_current_changed()

    def follow_current_tab(self, current: Tab | None) -> None:
        if current is None:
            return
        new_index = self._tabs.index(current)
        if new_index == self._current_index:
            return
        self._current_index = new_index
        self.notify_current_changed()
