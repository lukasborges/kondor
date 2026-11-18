import pytest
from PySide6.QtTest import QTest

from tests.browser.sidebar.sidebarharness import SETTLE_MS, SideBarHarness

pytestmark = pytest.mark.no_qt_log

FIVE_TABS = 5
FAR = 400
HALF = 200


def two_groups_around_a_loose_tab(side_bar: SideBarHarness):
    side_bar.add_tabs(FIVE_TABS)
    first = side_bar.tabs.newGroupForTab(0)
    side_bar.tabs.addTabToGroup(1, first)
    second = side_bar.tabs.newGroupForTab(3)
    side_bar.tabs.addTabToGroup(4, second)
    QTest.qWait(SETTLE_MS)
    return first, second


def members(side_bar: SideBarHarness, group: object) -> list[int]:
    return [row for row, tab in enumerate(side_bar.order()) if tab.group is group]


def is_contiguous(rows: list[int]) -> bool:
    return rows == list(range(rows[0], rows[0] + len(rows)))


def test_a_label_row_comes_before_each_group(side_bar: SideBarHarness) -> None:
    two_groups_around_a_loose_tab(side_bar)
    assert side_bar.rows() == FIVE_TABS + 2


def test_dragging_a_grouped_tab_past_its_label_keeps_it_in_the_group(
    side_bar: SideBarHarness,
) -> None:
    first, _ = two_groups_around_a_loose_tab(side_bar)
    before = side_bar.order()
    side_bar.drag_row(2, -FAR)
    assert side_bar.order() == [before[1], before[0], *before[2:]]
    assert before[1].group is first


def test_dragging_a_grouped_tab_down_stays_inside_its_group(side_bar: SideBarHarness) -> None:
    first, _ = two_groups_around_a_loose_tab(side_bar)
    before = side_bar.order()
    side_bar.drag_row(1, FAR)
    assert side_bar.order() == [before[1], before[0], *before[2:]]
    assert before[0].group is first


def test_dragging_a_label_moves_the_whole_group_down(side_bar: SideBarHarness) -> None:
    first, second = two_groups_around_a_loose_tab(side_bar)
    side_bar.drag_row(0, FAR)
    assert is_contiguous(members(side_bar, first))
    assert is_contiguous(members(side_bar, second))
    assert members(side_bar, first) == [3, 4]


def test_dragging_a_label_never_puts_the_group_inside_another(side_bar: SideBarHarness) -> None:
    first, second = two_groups_around_a_loose_tab(side_bar)
    side_bar.drag_row(0, HALF)
    assert is_contiguous(members(side_bar, first))
    assert is_contiguous(members(side_bar, second))


def test_closing_the_first_tab_of_the_list_leaves_no_stray_bar(side_bar: SideBarHarness) -> None:
    side_bar.add_tabs(FIVE_TABS)
    group = side_bar.tabs.newGroupForTab(1)
    side_bar.tabs.addTabToGroup(2, group)
    side_bar.tabs.closeTab(0)
    QTest.qWait(SETTLE_MS)
    assert side_bar.visible_bars() == side_bar.tabs.tabCountOf(group)
    assert side_bar.rows() == side_bar.tabs.count + 1
