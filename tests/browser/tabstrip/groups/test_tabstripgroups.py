import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest

from tests.browser.tabstrip.tabstripharness import SETTLE_MS, STRIP_ROW_Y, TabStripHarness

pytestmark = pytest.mark.no_qt_log

UNNAMED_LABEL_WIDTH = 32.0
THREE_TABS = 3
LABEL_CLICK_OFFSET = 10


def group_first_two_tabs(strip: TabStripHarness):
    strip.add_tabs(THREE_TABS)
    group = strip.tabs.newGroupForTab(0)
    strip.tabs.addTabToGroup(1, group)
    QTest.qWait(SETTLE_MS)
    return group


def test_first_tab_of_a_group_makes_room_for_the_label(strip: TabStripHarness) -> None:
    group_first_two_tabs(strip)
    assert strip.width_of(0) == pytest.approx(strip.tab_width() + UNNAMED_LABEL_WIDTH * 1.0, abs=8)
    assert strip.width_of(1) == strip.tab_width()


def test_clicking_the_label_collapses_the_group(strip: TabStripHarness) -> None:
    group = group_first_two_tabs(strip)
    strip.tabs.setCurrentIndex(2)
    strip.click(QPoint(int(strip.left_of(0)) + LABEL_CLICK_OFFSET, STRIP_ROW_Y))
    QTest.qWait(SETTLE_MS)
    assert group.collapsed
    assert strip.width_of(1) == 0


def test_collapsed_tabs_leave_no_gap(strip: TabStripHarness) -> None:
    group = group_first_two_tabs(strip)
    strip.tabs.setCurrentIndex(2)
    strip.tabs.setGroupCollapsed(group, True)
    QTest.qWait(SETTLE_MS)
    assert strip.left_of(2) - strip.left_of(0) == pytest.approx(strip.width_of(0))
