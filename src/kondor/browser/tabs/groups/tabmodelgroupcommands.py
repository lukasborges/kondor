from typing import Any

from PySide6.QtCore import Slot

from kondor.browser.tabs.groups.tabgroup import TabGroup
from kondor.browser.tabs.groups.tabmodelgroupmoves import TabModelGroupMoves
from kondor.browser.tabs.tab import Tab


class TabModelGroupCommands(TabModelGroupMoves):
    @Slot(int, result=TabGroup)
    def newGroupForTab(self, index: int) -> TabGroup | None:
        if not self.can_group(index):
            return None
        group = self._create_group()
        self.assign_group(self._tabs[index], group)
        self._touch_groups()
        return group

    def can_group(self, index: int) -> bool:
        return self.is_valid_index(index) and not self._tabs[index].pinned

    @Slot(int, TabGroup)
    def addTabToGroup(self, index: int, group: TabGroup) -> None:
        if not self.can_group(index) or self._tabs[index].group is group:
            return
        tab = self._tabs[index]
        self.assign_group(tab, group)
        self.move_to_group_end(tab, group)

    def move_to_group_end(self, tab: Tab, group: TabGroup) -> None:
        source = self._tabs.index(tab)
        others = [row for row in self.members_of(group) if row != source]
        if not others:
            return
        target = others[-1] if source < others[-1] else others[-1] + 1
        if source != target:
            self.move_row(source, target)

    @Slot(int)
    def removeTabFromGroup(self, index: int) -> None:
        if not self.is_valid_index(index) or self._tabs[index].group is None:
            return
        self.leave_group(self._tabs[index])

    def leave_group(self, tab: Tab) -> None:
        group = tab.group
        if group is None:
            return
        self.move_after_group(tab, group)
        self.assign_group(tab, None)

    def move_after_group(self, tab: Tab, group: TabGroup) -> None:
        last = self.members_of(group)[-1]
        self.move_row_unless_there(self._tabs.index(tab), last)

    @Slot(TabGroup)
    def ungroup(self, group: TabGroup) -> None:
        for tab in [tab for tab in self._tabs if tab.group is group]:
            self.assign_group(tab, None)

    @Slot(TabGroup)
    def closeGroup(self, group: TabGroup) -> None:
        for row in reversed(self.members_of(group)):
            self.closeTab(row)

    @Slot(TabGroup, bool)
    def setGroupCollapsed(self, group: TabGroup, collapsed: bool) -> None:
        if collapsed and not self.leave_current_tab_outside(group):
            return
        group.set_collapsed(collapsed)

    def leave_current_tab_outside(self, group: TabGroup) -> bool:
        current = self._current_tab()
        if current is None or current.group is not group:
            return True
        outside = self.nearest_tab_outside(group)
        if outside < 0:
            return False
        self.setCurrentIndex(outside)
        return True

    def nearest_tab_outside(self, group: TabGroup) -> int:
        members = self.members_of(group)
        after = members[-1] + 1
        return after if after < len(self._tabs) else members[0] - 1

    @Slot(TabGroup, int)
    def moveGroup(self, group: TabGroup, target: int) -> None:
        members = self.members_of(group)
        if not members:
            return
        start = self.group_boundary_near(group, target)
        ordered = members if start < members[0] else list(reversed(members))
        for row in ordered:
            self.move_row_unless_there(row, start + row - members[0])

    def gather_group(self, group: TabGroup) -> None:
        members = self.members_of(group)
        for offset, row in enumerate(members):
            self.move_row_unless_there(row, members[0] + offset)

    def group_boundary_near(self, group: TabGroup, target: int) -> int:
        others = [tab for tab in self._tabs if tab.group is not group]
        start = max(self._pinned_count(), min(target, len(others)))
        return self.snap_outside_groups(others, start)

    def notify_current_changed(self) -> None:
        current = self._current_tab()
        if current is not None and current.group is not None:
            current.group.set_collapsed(False)
        super().notify_current_changed()

    @Slot("QVariantList", "QVariantList")
    def restoreGroups(self, specs: list[Any], tab_groups: list[Any]) -> None:
        groups = [self.create_group_from(spec) for spec in specs]
        for row, position in enumerate(tab_groups[: len(self._tabs)]):
            if isinstance(position, int) and 0 <= position < len(groups):
                self.assign_group(self._tabs[row], groups[position])
        for group in groups:
            self._prune_group(group)
            self.gather_group(group)

    def create_group_from(self, spec: Any) -> TabGroup:
        fields = spec if isinstance(spec, dict) else {}
        group = self._create_group(str(fields.get("name", "")), str(fields.get("color", "")))
        group.set_collapsed(fields.get("collapsed") is True)
        return group
