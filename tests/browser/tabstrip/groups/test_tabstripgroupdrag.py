import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest

from tests.browser.tabstrip.tabstripharness import SETTLE_MS, STRIP_ROW_Y, TabStripHarness

pytestmark = pytest.mark.no_qt_log

FIVE_TABS = 5
LABEL_CLICK_OFFSET = 10
FAR = 900
PAST_LAST_TAB = 150


def two_groups_around_a_loose_tab(strip: TabStripHarness):
    strip.add_tabs(FIVE_TABS)
    first = strip.tabs.newGroupForTab(0)
    strip.tabs.addTabToGroup(1, first)
    second = strip.tabs.newGroupForTab(3)
    strip.tabs.addTabToGroup(4, second)
    QTest.qWait(SETTLE_MS)
    return first, second


def drag_to(strip: TabStripHarness, press: QPoint, dx: int) -> None:
    step = 5 if dx > 0 else -5
    for distance in range(step, dx, step):
        strip.move_mouse(press + QPoint(distance, 0))
    strip.move_mouse(press + QPoint(dx, 0))
    QTest.qWait(SETTLE_MS)


def members(strip: TabStripHarness, group: object) -> list[int]:
    return [row for row, tab in enumerate(strip.order()) if tab.group is group]


def is_contiguous(rows: list[int]) -> bool:
    return rows == list(range(rows[0], rows[0] + len(rows)))


def test_dragging_a_grouped_tab_past_its_label_keeps_it_after_the_label(
    strip: TabStripHarness,
) -> None:
    first, _ = two_groups_around_a_loose_tab(strip)
    before = strip.order()
    session = strip.press_on_tab(1, LABEL_CLICK_OFFSET)
    drag_to(strip, session.press, -FAR)
    strip.release_and_settle(session, -FAR)
    assert strip.order() == [before[1], before[0], *before[2:]]
    assert before[1].group is first
    assert strip.left_of(0) >= strip.label_left(first) + strip.label_width(first) - 0.5


def test_dragging_a_label_moves_the_whole_group(strip: TabStripHarness) -> None:
    first, second = two_groups_around_a_loose_tab(strip)
    press = QPoint(int(strip.label_left(first)) + LABEL_CLICK_OFFSET, STRIP_ROW_Y)
    dx = int(strip.left_of(4)) + PAST_LAST_TAB - press.x()
    strip.press(press)
    drag_to(strip, press, dx)
    strip.release(press + QPoint(dx, 0))
    QTest.qWait(SETTLE_MS)
    assert members(strip, first) == [3, 4]
    assert members(strip, second) == [1, 2]


def test_dragging_a_label_never_puts_the_group_inside_another(strip: TabStripHarness) -> None:
    first, second = two_groups_around_a_loose_tab(strip)
    press = QPoint(int(strip.label_left(first)) + LABEL_CLICK_OFFSET, STRIP_ROW_Y)
    strip.press(press)
    drag_to(strip, press, int(strip.left_of(4)) - press.x())
    strip.release(press + QPoint(int(strip.left_of(4)) - press.x(), 0))
    QTest.qWait(SETTLE_MS)
    assert members(strip, second) != [] and is_contiguous(members(strip, second))
    assert is_contiguous(members(strip, first))


def test_the_label_never_leaves_its_tabs_while_dragging(strip: TabStripHarness) -> None:
    first, _ = two_groups_around_a_loose_tab(strip)
    gap = strip.left_of(0) - strip.chip_left(first)
    press = QPoint(int(strip.label_left(first)) + LABEL_CLICK_OFFSET, STRIP_ROW_Y)
    strip.press(press)
    drag_to(strip, press, 120)
    assert strip.left_of(0) - strip.chip_left(first) == pytest.approx(gap)
    strip.release(press + QPoint(120, 0))
