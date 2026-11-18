import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest

from tests.browser.tabstrip.tabstripharness import SETTLE_MS, STRIP_ROW_Y, TabStripHarness

pytestmark = pytest.mark.no_qt_log

UNNAMED_LABEL_WIDTH = 32.0
THREE_TABS = 3
OTHER_TAB = 2
LABEL_CLICK_OFFSET = 10


def group_first_two_tabs(strip: TabStripHarness):
    strip.add_tabs(THREE_TABS)
    group = strip.tabs.newGroupForTab(0)
    strip.tabs.addTabToGroup(1, group)
    QTest.qWait(SETTLE_MS)
    return group


def test_label_is_its_own_item_before_the_first_tab_of_the_group(strip: TabStripHarness) -> None:
    group = group_first_two_tabs(strip)
    assert strip.label_width(group) == pytest.approx(UNNAMED_LABEL_WIDTH, abs=8)
    assert strip.width_of(0) == strip.tab_width()
    assert strip.left_of(0) == pytest.approx(strip.label_left(group) + strip.label_width(group))


def test_clicking_the_label_collapses_the_group(strip: TabStripHarness) -> None:
    group = group_first_two_tabs(strip)
    strip.tabs.setCurrentIndex(OTHER_TAB)
    strip.click(QPoint(int(strip.label_left(group)) + LABEL_CLICK_OFFSET, STRIP_ROW_Y))
    QTest.qWait(SETTLE_MS)
    assert group.collapsed
    assert strip.width_of(1) == 0
    assert strip.tabs.currentIndex == OTHER_TAB


def test_collapsed_tabs_leave_no_gap(strip: TabStripHarness) -> None:
    group = group_first_two_tabs(strip)
    strip.tabs.setCurrentIndex(2)
    strip.tabs.setGroupCollapsed(group, True)
    QTest.qWait(SETTLE_MS)
    assert strip.left_of(2) - strip.label_left(group) == pytest.approx(strip.label_width(group))


def test_closing_the_first_tab_of_the_strip_leaves_no_stray_bar(strip: TabStripHarness) -> None:
    strip.add_tabs(THREE_TABS + 1)
    group = strip.tabs.newGroupForTab(1)
    strip.tabs.addTabToGroup(2, group)
    strip.tabs.closeTab(0)
    QTest.qWait(SETTLE_MS)
    assert strip.label_left(group) == strip.strip_property("contentMargin")
    assert strip.visible_bars() == strip.tabs.tabCountOf(group)
