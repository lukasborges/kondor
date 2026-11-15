import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import TabStripHarness

pytestmark = pytest.mark.no_qt_log

STANDARD_WIDTH = 240.0
SEVEN_TABS = 7
OVER_STRIP = QPoint(500, 10)
BELOW_STRIP = QPoint(500, 58)
FREEZE_WAIT_MS = 1200


def close_while_the_pointer_is_over_the_strip(strip: TabStripHarness) -> None:
    strip.move_mouse(OVER_STRIP)
    strip.close_with_mouse(strip.tabs.currentTab)
    QTest.qWait(FREEZE_WAIT_MS)


def test_closing_with_the_mouse_keeps_the_width(strip: TabStripHarness) -> None:
    strip.add_tabs(SEVEN_TABS)
    shrunk = strip.tab_width()
    assert shrunk < STANDARD_WIDTH
    strip.close_with_mouse(strip.tabs.currentTab)
    assert strip.tabs.count == SEVEN_TABS - 1
    assert strip.tab_width() == shrunk


def test_closing_with_the_keyboard_recomputes_the_width(strip: TabStripHarness) -> None:
    strip.add_tabs(SEVEN_TABS)
    shrunk = strip.tab_width()
    strip.close_with_mouse(strip.tabs.currentTab)
    strip.tabs.closeTab(0)
    assert strip.tabs.count == SEVEN_TABS - 2
    assert strip.tab_width() > shrunk


def test_width_stays_while_the_pointer_is_over_the_strip(strip: TabStripHarness) -> None:
    strip.add_tabs(SEVEN_TABS)
    before = strip.tab_width()
    close_while_the_pointer_is_over_the_strip(strip)
    assert strip.tab_width() == before


def test_width_is_recomputed_when_the_pointer_leaves(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(SEVEN_TABS)
    before = strip.tab_width()
    close_while_the_pointer_is_over_the_strip(strip)
    strip.move_mouse(BELOW_STRIP)
    qtbot.waitUntil(lambda: strip.tab_width() > before)
