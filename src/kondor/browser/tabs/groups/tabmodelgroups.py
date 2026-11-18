from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.tabs.groups.tabgroup import GROUP_COLORS, TabGroup
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodelrows import TabModelRows


class TabModelGroups(TabModelRows):
    groupsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._groups: list[TabGroup] = []
        self._group_revision = 0

    groups = Property("QVariantList", lambda self: list(self._groups), notify=groupsChanged)
    groupRevision = Property(int, lambda self: self._group_revision, notify=groupsChanged)

    def _touch_groups(self) -> None:
        self._group_revision += 1
        self.groupsChanged.emit()

    def _create_group(self, name: str = "", color: str = "") -> TabGroup:
        group = TabGroup(name, color or self._first_unused_color(), self)
        for signal in (group.nameChanged, group.colorChanged, group.collapsedChanged):
            signal.connect(self._touch_groups)
        self._groups.append(group)
        return group

    def _first_unused_color(self) -> str:
        used = {group.color for group in self._groups}
        unused = [color for color in GROUP_COLORS if color not in used]
        return unused[0] if unused else GROUP_COLORS[len(self._groups) % len(GROUP_COLORS)]

    def members_of(self, group: TabGroup) -> list[int]:
        return [row for row, tab in enumerate(self._tabs) if tab.group is group]

    @Slot(TabGroup, result=int)
    def tabCountOf(self, group: TabGroup) -> int:
        return len(self.members_of(group))

    @Slot(TabGroup, result=int)
    def firstIndexOf(self, group: TabGroup) -> int:
        members = self.members_of(group)
        return members[0] if members else -1

    @Slot(int, result=bool)
    def isGroupStart(self, index: int) -> bool:
        if not self.is_valid_index(index) or self._tabs[index].group is None:
            return False
        return index == 0 or self._tabs[index - 1].group is not self._tabs[index].group

    @Slot(int, result=bool)
    def isHiddenByGroup(self, index: int) -> bool:
        if not self.is_valid_index(index):
            return False
        group = self._tabs[index].group
        return group is not None and group.collapsed

    @Slot(int, result=Tab)
    def tabAt(self, index: int) -> Tab | None:
        return self._tabs[index] if self.is_valid_index(index) else None

    @Slot(int, result=TabGroup)
    def groupAt(self, index: int) -> TabGroup | None:
        return self._tabs[index].group if self.is_valid_index(index) else None

    def _collapsed_tab_count(self) -> int:
        return sum(1 for tab in self._tabs if tab.group is not None and tab.group.collapsed)

    collapsedTabCount = Property(int, _collapsed_tab_count, notify=groupsChanged)

    def _prune_group(self, group: TabGroup | None) -> None:
        if group is None or group not in self._groups or self.members_of(group):
            return
        self._groups.remove(group)
        group.deleteLater()
        self._touch_groups()

    def assign_group(self, tab: Tab, group: TabGroup | None) -> None:
        previous = tab.group
        if previous is group:
            return
        tab.set_group(group)
        self._prune_group(previous)
        self._touch_groups()

    def remove_row(self, index: int) -> Tab:
        tab = super().remove_row(index)
        self._prune_group(tab.group)
        if tab.group is not None:
            self._touch_groups()
        return tab

    def insert_row(self, index: int, tab: Tab) -> None:
        super().insert_row(index, tab)
        self.join_group_around_inserted(tab)

    def join_group_around_inserted(self, tab: Tab) -> None:
        row = self._tabs.index(tab)
        before = self._tabs[row - 1].group if row > 0 else None
        after = self._tabs[row + 1].group if row + 1 < len(self._tabs) else None
        if before is not None and before is after and not tab.pinned:
            self.assign_group(tab, before)
