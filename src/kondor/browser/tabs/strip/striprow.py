from dataclasses import dataclass
from enum import IntEnum

from PySide6.QtCore import Qt

from kondor.browser.tabs.groups.tabgroup import TabGroup
from kondor.browser.tabs.tab import Tab

LABEL = "label"
TAB = "tab"


class StripRole(IntEnum):
    KIND = Qt.ItemDataRole.UserRole + 1
    TAB = Qt.ItemDataRole.UserRole + 2
    GROUP = Qt.ItemDataRole.UserRole + 3
    IS_HIDDEN = Qt.ItemDataRole.UserRole + 4
    IS_PINNED = Qt.ItemDataRole.UserRole + 5
    TAB_INDEX = Qt.ItemDataRole.UserRole + 6


@dataclass(frozen=True)
class StripRow:
    kind: str
    tab: Tab | None
    group: TabGroup | None
    is_hidden: bool
    is_pinned: bool
    tab_index: int

    @property
    def key(self) -> tuple[str, object]:
        return (self.kind, self.tab if self.kind == TAB else self.group)

    def value_for(self, role: int) -> object:
        wanted = StripRole(role) if role in StripRole else None
        values = {
            StripRole.KIND: self.kind,
            StripRole.TAB: self.tab,
            StripRole.GROUP: self.group,
            StripRole.IS_HIDDEN: self.is_hidden,
            StripRole.IS_PINNED: self.is_pinned,
            StripRole.TAB_INDEX: self.tab_index,
        }
        return values.get(wanted) if wanted is not None else None


def label_row(group: TabGroup, first_tab_index: int) -> StripRow:
    return StripRow(LABEL, None, group, False, False, first_tab_index)


def tab_row(tab: Tab, index: int) -> StripRow:
    hidden = tab.group is not None and tab.group.collapsed
    return StripRow(TAB, tab, tab.group, hidden, tab.pinned, index)


def build_rows(tabs: list[Tab]) -> list[StripRow]:
    rows: list[StripRow] = []
    labelled: set[TabGroup] = set()
    for index, tab in enumerate(tabs):
        if tab.group is not None and tab.group not in labelled:
            labelled.add(tab.group)
            rows.append(label_row(tab.group, index))
        rows.append(tab_row(tab, index))
    return rows
