import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import STRIP_ROW_Y, DragSession, TabStripHarness

pytestmark = pytest.mark.no_qt_log

FIVE_TABS = 5
THIRTY_TABS = 30
CLOSE_BUTTON_INSET = 14
CLOSE_VARIANTS = [0, 1, 2, 3]
LAST_CLICK_VARIANT = 3
VISIBLE_EDGE = 40
SCROLL_POSITION = 253.0


def click_close_button_of(strip: TabStripHarness, index: int) -> None:
    x = int(strip.left_of(index) + strip.tab_width()) - CLOSE_BUTTON_INSET
    strip.click(QPoint(x, STRIP_ROW_Y))


def close_according_to_variant(strip: TabStripHarness, variant: int) -> None:
    if variant == 0:
        click_close_button_of(strip, 1)
    elif variant == 1:
        click_close_button_of(strip, 2)
    else:
        middle = QPoint(int(strip.left_of(2)) + 60, STRIP_ROW_Y)
        strip.click(middle, Qt.MouseButton.MiddleButton)


def drag_right_by_five_steps_up_to(
    strip: TabStripHarness, session: DragSession, limit: int
) -> None:
    for dx in range(5, limit + 1, 5):
        strip.move_mouse(session.press + QPoint(dx, 0))
    QTest.qWait(60)


def test_short_move_is_a_click(strip: TabStripHarness) -> None:
    strip.add_tabs(FIVE_TABS)
    session = strip.press_on_tab(1, 100)
    strip.move_mouse(session.press + QPoint(2, 0))
    strip.release_drag(session, 2)
    QTest.qWait(50)
    assert strip.order() == session.before
    assert strip.tabs.currentIndex == 1


@pytest.mark.parametrize("variant", CLOSE_VARIANTS)
def test_closing_after_a_click_does_not_crash(strip: TabStripHarness, variant: int) -> None:
    strip.add_tabs(FIVE_TABS)
    strip.tabs.setCurrentIndex(4 if variant < LAST_CLICK_VARIANT else 1)
    strip.click(QPoint(int(strip.left_of(1)) + 60, STRIP_ROW_Y))
    QTest.qWait(1000)
    close_according_to_variant(strip, variant)
    QTest.qWait(300)
    assert strip.tabs.count == FIVE_TABS - 1


def test_release_animates_into_the_slot(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(FIVE_TABS)
    session = strip.press_on_tab(1, 100)
    drag_right_by_five_steps_up_to(strip, session, 40)
    assert strip.drag_shift_of(session) != 0.0
    strip.release_drag(session, 40)
    assert strip.drag_shift_of(session) != 0.0
    strip.settle(session)


def test_current_tab_is_visible_after_a_release(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.resize(1100)
    strip.add_tabs(THIRTY_TABS)
    strip.scroll_to(SCROLL_POSITION)
    qtbot.waitUntil(lambda: strip.scrolled() == SCROLL_POSITION)
    index = 0
    while index < THIRTY_TABS - 1 and strip.left_of(index) < VISIBLE_EDGE:
        index += 1
    press = QPoint(int(strip.left_of(index)) + int(strip.tab_width()) - 30, STRIP_ROW_Y)
    strip.press(press)
    for x in range(press.x(), VISIBLE_EDGE, -10):
        strip.move_mouse(QPoint(x, STRIP_ROW_Y))
    strip.move_mouse(QPoint(VISIBLE_EDGE, STRIP_ROW_Y))
    QTest.qWait(60)
    strip.release(QPoint(VISIBLE_EDGE, STRIP_ROW_Y))
    qtbot.waitUntil(lambda: strip.call("isStartOfTabInView", strip.tabs.currentIndex))


def test_closing_the_dragged_tab_resets_the_drag_state(strip: TabStripHarness) -> None:
    strip.add_tabs(FIVE_TABS)
    session = strip.press_on_tab(1, 100)
    drag_right_by_five_steps_up_to(strip, session, 60)
    assert strip.strip_property("tabDragActive")
    strip.tabs.closeTabObject(strip.tab_at(strip.tabs.currentIndex))
    strip.release_drag(session, 60)
    QTest.qWait(300)
    assert strip.strip_property("tabDragActive") is False
    assert strip.tabs.count == FIVE_TABS - 1
