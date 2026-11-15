import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import STRIP_ROW_Y, DragSession, TabStripHarness

pytestmark = pytest.mark.no_qt_log

FIVE_TABS = 5
PRESS_OFFSET = 100
RIGHT_LIMIT = 1090
LEFT_MARGIN = 2
PINNED_DRAG = 400


def half_width(strip: TabStripHarness) -> int:
    return int(strip.tab_width() / 2)


def press_second_of_five_with_the_fifth_selected(strip: TabStripHarness) -> DragSession:
    strip.add_tabs(FIVE_TABS)
    strip.tabs.setCurrentIndex(4)
    return strip.press_on_tab(1, PRESS_OFFSET)


def assert_dragged_left_is(strip: TabStripHarness, session: DragSession, expected: float) -> None:
    assert abs(strip.dragged_left(session) - expected) <= 1.0


def drag_to_the_left_edge(strip: TabStripHarness, session: DragSession) -> None:
    dx = -10
    while session.press.x() + dx > LEFT_MARGIN:
        strip.move_mouse(session.press + QPoint(dx, 0))
        dx -= 10
    QTest.qWait(100)


def drag_to_the_right_edge(strip: TabStripHarness, session: DragSession) -> None:
    for dx in range(-session.press.x() + 5, RIGHT_LIMIT - session.press.x() + 1, 20):
        strip.move_mouse(session.press + QPoint(dx, 0))
    QTest.qWait(100)


def test_dragged_tab_follows_the_pointer_and_selects_itself(
    strip: TabStripHarness, qtbot: QtBot
) -> None:
    session = press_second_of_five_with_the_fifth_selected(strip)
    distance = half_width(strip) - 5
    strip.drag_by(session, distance)
    assert_dragged_left_is(strip, session, session.start_left + distance)
    assert strip.order() == session.before
    assert strip.tabs.currentTab is session.before[1]
    strip.release_and_settle(session, distance)


def test_dragged_tab_swaps_past_the_center_of_its_neighbour(
    strip: TabStripHarness, qtbot: QtBot
) -> None:
    session = press_second_of_five_with_the_fifth_selected(strip)
    distance = half_width(strip) + 5
    strip.drag_by(session, distance)
    assert strip.tab_at(1) is session.before[2]
    assert strip.tab_at(2) is session.before[1]
    assert_dragged_left_is(strip, session, session.start_left + distance)
    strip.release_and_settle(session, distance)


def test_dragged_tab_swaps_again_past_the_next_center(strip: TabStripHarness, qtbot: QtBot) -> None:
    session = press_second_of_five_with_the_fifth_selected(strip)
    target = int(strip.tab_width() * 1.5)
    strip.drag_by(session, target - 5)
    assert strip.tab_at(2) is session.before[1]
    strip.drag_by(session, target + 5)
    assert strip.tab_at(3) is session.before[1]
    assert_dragged_left_is(strip, session, session.start_left + target + 5)
    strip.release_and_settle(session, target + 5)


def test_releasing_keeps_the_new_order_and_selection(strip: TabStripHarness, qtbot: QtBot) -> None:
    session = press_second_of_five_with_the_fifth_selected(strip)
    target = int(strip.tab_width() * 1.5) + 5
    strip.drag_by(session, target)
    strip.release_and_settle(session, target)
    assert strip.tab_at(3) is session.before[1]
    assert strip.tabs.currentTab is session.before[1]


def test_dragged_tab_is_clamped_to_the_strip(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(FIVE_TABS)
    first, last = strip.left_of(0), strip.left_of(4)
    session = strip.press_on_tab(3, PRESS_OFFSET)
    drag_to_the_left_edge(strip, session)
    assert strip.tab_at(0) is session.before[3]
    assert_dragged_left_is(strip, session, first)
    drag_to_the_right_edge(strip, session)
    assert strip.tab_at(4) is session.before[3]
    assert_dragged_left_is(strip, session, last)
    strip.release_and_settle(session, RIGHT_LIMIT - session.press.x())


def test_pinned_tabs_stay_in_their_section(strip: TabStripHarness) -> None:
    strip.add_tabs(FIVE_TABS)
    strip.tabs.setPinned(0, True)
    strip.tabs.setPinned(1, True)
    QTest.qWait(100)
    session = strip.press_on_tab(0, STRIP_ROW_Y)
    for dx in range(0, PINNED_DRAG + 1, 20):
        strip.move_mouse(session.press + QPoint(dx, 0))
    QTest.qWait(100)
    assert strip.tab_at(1) is session.before[0]
    assert strip.tab_at(2) is session.before[2]
    strip.release_drag(session, PINNED_DRAG)
    QTest.qWait(100)
    assert strip.tab_at(0).pinned
    assert strip.tab_at(1).pinned
