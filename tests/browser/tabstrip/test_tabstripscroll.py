import pytest
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import STRIP_ROW_Y, TabStripHarness

pytestmark = pytest.mark.no_qt_log

MANY_TABS = 20
LAST_TAB = 19
ON_TAB_X = 100
EMPTY_X = 1000


def is_empty_at(strip: TabStripHarness, x: int, y: int) -> bool:
    return bool(strip.call("emptyAt", strip.call("sceneX", x, y), strip.call("sceneY", x, y)))


def test_new_current_tab_is_scrolled_into_view(strip: TabStripHarness, qtbot: QtBot) -> None:
    strip.add_tabs(MANY_TABS)
    assert strip.view_property("contentX") > 0
    qtbot.waitUntil(lambda: strip.call("isFullyInView", LAST_TAB))


def test_empty_area_is_only_outside_tabs_and_buttons(strip: TabStripHarness) -> None:
    strip.add_tabs(3)
    button_x = int(strip.call("buttonCenterX", "newTabButton"))
    button_y = int(strip.call("buttonCenterY", "newTabButton"))
    assert not is_empty_at(strip, ON_TAB_X, STRIP_ROW_Y)
    assert not strip.call("emptyAt", button_x, button_y)
    assert is_empty_at(strip, EMPTY_X, STRIP_ROW_Y)
