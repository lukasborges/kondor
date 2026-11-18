from kondor.browser.tabs.groups.tabmodelgroups import TabModelGroups
from kondor.browser.tabs.tab import Tab


class TabModelGroupMoves(TabModelGroups):
    def move_row_unless_there(self, source: int, target: int) -> None:
        if source != target:
            self.move_row(source, target)

    def clamp_move_target(self, source: int, target: int) -> int:
        tab = self._tabs[source]
        if tab.group is not None:
            members = self.members_of(tab.group)
            return max(members[0], min(target, members[-1]))
        others = self._tabs[:source] + self._tabs[source + 1 :]
        return self.snap_outside_groups(others, target)

    def step_target(self, index: int, delta: int) -> int:
        target = index + delta
        if not self.is_valid_index(target) or self._tabs[index].group is not None:
            return target
        group = self._tabs[target].group
        if group is None:
            return target
        members = self.members_of(group)
        return members[-1] if delta > 0 else members[0]

    def snap_outside_groups(self, tabs: list[Tab], position: int) -> int:
        if not 0 < position < len(tabs) or not self.is_inside_group(tabs, position):
            return position
        group = tabs[position].group
        first = position
        while first > 0 and tabs[first - 1].group is group:
            first -= 1
        end = position
        while end < len(tabs) and tabs[end].group is group:
            end += 1
        return first if position - first <= end - position else end

    def is_inside_group(self, tabs: list[Tab], position: int) -> bool:
        before = tabs[position - 1].group
        return before is not None and before is tabs[position].group
