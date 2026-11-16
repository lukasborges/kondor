import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import STRIP_ROW_Y, DragSession, TabStripHarness

pytestmark = pytest.mark.no_qt_log

THIRTY_TABS = 30
STRIP_WIDTH = 1280
WINDOW_HEIGHT = 60
AUTO_SCROLL_START_MS = 2000
AUTO_SCROLL_END_MS = 10000
AUTO_SCROLLED_PIXELS = 50
PINNED_SCROLL_LIMIT = 80
PINNED_TABS = 2


def scroll_thirty_tabs_to_the_end(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.resize(STRIP_WIDTH)
    strip.add_tabs(THIRTY_TABS)
    max_scroll = float(strip.strip_property("maxScroll"))
    assert max_scroll > 0
    strip.scroll_to(max_scroll)
    qtbot.waitUntil(lambda: strip.scrolled() == max_scroll)


def start_with_thirty_tabs_at_the_start(strip: TabStripHarness, qtbot: QtBot) -> None:
    open_thirty_tabs(strip)
    strip.scroll_to(0.0)
    qtbot.waitUntil(lambda: strip.scrolled() == 0.0)


def start_with_thirty_tabs_two_pinned(strip: TabStripHarness, qtbot: QtBot) -> None:
    open_thirty_tabs(strip)
    for index in range(PINNED_TABS):
        strip.tabs.setPinned(index, True)
    strip.tabs.setCurrentIndex(PINNED_TABS)
    qtbot.waitUntil(lambda: strip.scrolled() <= PINNED_SCROLL_LIMIT)


def open_thirty_tabs(strip: TabStripHarness) -> None:
    strip.window.resize(STRIP_WIDTH, WINDOW_HEIGHT)
    strip.resize(STRIP_WIDTH)
    strip.add_tabs(THIRTY_TABS)


def drag_tab_to_the_right_edge(strip: TabStripHarness, index: int) -> DragSession:
    session = strip.press_on_tab(index, 30)
    view_width = int(strip.view_property("width"))
    for x in range(session.press.x(), view_width - 10, 20):
        strip.move_mouse(QPoint(x, STRIP_ROW_Y))
    strip.move_mouse(QPoint(view_width - 10, STRIP_ROW_Y))
    return session


def wait_for_auto_scroll_to_the_end(
    strip: TabStripHarness, session: DragSession, qtbot: QtBot
) -> None:
    max_scroll = float(strip.strip_property("maxScroll"))
    qtbot.waitUntil(lambda: strip.scrolled() > AUTO_SCROLLED_PIXELS, timeout=AUTO_SCROLL_START_MS)
    qtbot.waitUntil(lambda: strip.scrolled() == max_scroll, timeout=AUTO_SCROLL_END_MS)
    qtbot.waitUntil(lambda: strip.tab_at(29) is session.dragged)


def test_dragging_in_a_scrolled_strip_goes_the_right_way(
    strip: TabStripHarness, qtbot: QtBot
) -> None:
    scroll_thirty_tabs_to_the_end(strip, qtbot)
    session = strip.press_on_tab(27, 30)
    for dx in range(-10, -131, -10):
        strip.move_mouse(session.press + QPoint(dx, 0))
    QTest.qWait(100)
    assert strip.tab_at(26) is session.before[27]
    assert abs(strip.dragged_left(session) - (session.start_left - 130)) <= 1.0
    strip.release_drag(session, -130)
    strip.settle(session)


def test_dragging_to_the_edge_auto_scrolls(strip: TabStripHarness, qtbot: QtBot) -> None:
    start_with_thirty_tabs_at_the_start(strip, qtbot)
    session = drag_tab_to_the_right_edge(strip, 0)
    wait_for_auto_scroll_to_the_end(strip, session, qtbot)
    assert abs(strip.dragged_left(session) - strip.left_of(29)) <= 1.0
    strip.release(QPoint(int(strip.view_property("width")) - 10, STRIP_ROW_Y))
    strip.settle(session)


def test_leaving_the_edge_zone_stops_the_scrolling(strip: TabStripHarness, qtbot: QtBot) -> None:
    start_with_thirty_tabs_at_the_start(strip, qtbot)
    session = drag_tab_to_the_right_edge(strip, 0)
    wait_for_auto_scroll_to_the_end(strip, session, qtbot)
    middle = QPoint(int(strip.view_property("width")) // 2, STRIP_ROW_Y)
    strip.move_mouse(middle)
    QTest.qWait(100)
    stopped = strip.scrolled()
    QTest.qWait(150)
    assert strip.scrolled() == stopped
    strip.release(middle)
    strip.settle(session)


def test_dragging_to_the_edge_auto_scrolls_with_pinned_tabs(
    strip: TabStripHarness, qtbot: QtBot
) -> None:
    start_with_thirty_tabs_two_pinned(strip, qtbot)
    session = drag_tab_to_the_right_edge(strip, PINNED_TABS)
    wait_for_auto_scroll_to_the_end(strip, session, qtbot)
    assert abs(strip.dragged_left(session) - strip.left_of(29)) <= 1.0
    strip.release(QPoint(int(strip.view_property("width")) - 10, STRIP_ROW_Y))
    strip.settle(session)
