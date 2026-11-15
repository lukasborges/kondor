import math

import pytest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import TabStripHarness

pytestmark = pytest.mark.no_qt_log

STANDARD_WIDTH = 240.0
MINIMUM_WIDTH = 120.0
PINNED_WIDTH = 36.0
SEVEN_TABS = 7
MANY_TABS = 20
LONG_TITLE = "x" * 200
NARROW_STRIP = 700
LAST_TAB = 19


def is_enabled(strip: TabStripHarness, button: str) -> bool:
    return bool(strip.button_property(button, "enabled"))


def is_visible(strip: TabStripHarness, button: str) -> bool:
    return bool(strip.button_property(button, "visible"))


def test_few_tabs_keep_the_standard_width(strip: TabStripHarness) -> None:
    strip.add_tabs(3)
    assert strip.tab_width() == STANDARD_WIDTH
    assert not strip.strip_property("overflowing")
    assert not is_visible(strip, "scrollLeftButton")
    assert not is_visible(strip, "scrollRightButton")


def test_new_tab_button_follows_the_last_tab(strip: TabStripHarness) -> None:
    strip.add_tabs(3)
    bar_width = strip.call("barProp", "width")
    bar_x = strip.call("barProp", "x")
    assert strip.view_property("contentWidth") == 3 * STANDARD_WIDTH
    assert bar_width == 3 * STANDARD_WIDTH
    assert strip.button_property("newTabButton", "x") == bar_x + bar_width + 2


def test_tabs_shrink_together(strip: TabStripHarness) -> None:
    strip.add_tabs(SEVEN_TABS)
    expected = math.floor(strip.strip_property("tabsAreaWidth") / SEVEN_TABS)
    assert MINIMUM_WIDTH <= expected < STANDARD_WIDTH
    assert strip.tab_width() == expected
    assert not strip.strip_property("overflowing")
    assert all(strip.width_of(index) == expected for index in range(SEVEN_TABS))


def test_title_does_not_change_the_width(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(3)
    strip.tabs.currentTab.setTitle(LONG_TITLE)
    qtbot.wait(50)
    assert strip.tab_width() == STANDARD_WIDTH
    assert all(strip.width_of(index) == STANDARD_WIDTH for index in range(3))


def test_many_tabs_stop_at_the_minimum_and_show_scroll_buttons(strip: TabStripHarness) -> None:
    strip.add_tabs(MANY_TABS)
    assert strip.tab_width() == MINIMUM_WIDTH
    assert strip.strip_property("overflowing")
    assert is_visible(strip, "scrollLeftButton")
    assert is_visible(strip, "scrollRightButton")
    assert strip.view_property("contentWidth") == MANY_TABS * MINIMUM_WIDTH
    button_right = strip.button_property("newTabButton", "x") + strip.button_property(
        "newTabButton", "width"
    )
    assert button_right <= strip.strip_property("width")


def test_scroll_buttons_are_disabled_at_the_ends(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(MANY_TABS)
    qtbot.waitUntil(lambda: not is_enabled(strip, "scrollRightButton"))
    assert is_enabled(strip, "scrollLeftButton")
    strip.scroll_to(0)
    qtbot.waitUntil(lambda: not is_enabled(strip, "scrollLeftButton"))
    assert is_enabled(strip, "scrollRightButton")
    strip.click_button("scrollRightButton")
    qtbot.waitUntil(lambda: strip.scrolled() == MINIMUM_WIDTH)
    assert is_enabled(strip, "scrollLeftButton")


def test_current_tab_is_scrolled_into_view(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(MANY_TABS)
    strip.tabs.setCurrentIndex(0)
    qtbot.waitUntil(lambda: strip.scrolled() == 0.0)
    strip.tabs.setCurrentIndex(10)
    qtbot.waitUntil(lambda: strip.call("isFullyInView", 10))
    strip.resize(NARROW_STRIP)
    qtbot.waitUntil(lambda: strip.call("isFullyInView", 10))


def test_pinned_tabs_stay_narrow(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(3)
    strip.tabs.setPinned(0, True)
    qtbot.wait(50)
    assert strip.width_of(0) == PINNED_WIDTH
    assert strip.width_of(1) == STANDARD_WIDTH


def test_scrolled_out_tabs_are_clipped(strip: TabStripHarness) -> None:
    strip.add_tabs(MANY_TABS)
    assert strip.view_property("clip")


def test_last_tab_stays_clear_of_the_right_button(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(MANY_TABS)
    strip.tabs.setCurrentIndex(LAST_TAB)
    qtbot.waitUntil(lambda: not is_enabled(strip, "scrollRightButton"))
    assert strip.call("isInsideTabBar", LAST_TAB)
    assert not strip.call("overlapsButton", LAST_TAB, "scrollRightButton")
    assert is_enabled(strip, "scrollLeftButton")


def test_first_tab_stays_clear_of_the_left_button(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(MANY_TABS)
    strip.tabs.setCurrentIndex(0)
    qtbot.waitUntil(lambda: not is_enabled(strip, "scrollLeftButton"))
    assert strip.call("isInsideTabBar", 0)
    assert not strip.call("overlapsButton", 0, "scrollLeftButton")
    assert is_enabled(strip, "scrollRightButton")
