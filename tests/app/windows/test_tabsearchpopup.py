import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest

from tests.app.menu.mainmenuharness import MainMenuHarness

pytestmark = pytest.mark.no_qt_log

OPEN_TABS = 3
SETTLE_MILLISECONDS = 300

SEARCH_WINDOW_QML = """
import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    width: 800
    height: 600
    property bool privateWindow: false
    TabModel { id: tabs }
    Button { id: anchor; text: "anchor" }
    TabSearchPopup { id: popup; browserWindow: parent.Window.window }
    function open() { popup.openFor(anchor, false) }
}
"""


@pytest.fixture
def search_window(kondor_engine: QQmlEngine) -> MainMenuHarness:
    harness = MainMenuHarness(kondor_engine, SEARCH_WINDOW_QML)
    harness.show()
    harness.tabs.addTab(False, QUrl("https://kde.org/"))
    harness.tabs.addTab(False, QUrl("https://qt.io/"))
    harness.evaluate("open()")
    QTest.qWait(SETTLE_MILLISECONDS)
    return harness


def test_lists_every_tab_of_the_window(search_window: MainMenuHarness) -> None:
    assert search_window.evaluate("popup.results.length") == OPEN_TABS


def test_marks_exactly_the_current_tab(search_window: MainMenuHarness) -> None:
    assert search_window.evaluate("popup.results.filter(e => e.isCurrent).length") == 1


def test_filtering_narrows_the_list(search_window: MainMenuHarness) -> None:
    search_window.evaluate("popup.contentItem.children[0].text = 'qt'")

    assert search_window.evaluate("popup.results.length") == 1


def test_choosing_a_tab_closes_the_popup(
    search_window: MainMenuHarness,
) -> None:
    search_window.evaluate("popup.choose(popup.results[0].tab)")

    assert search_window.evaluate("popup.opened") is False


def test_stays_open_while_typing(search_window: MainMenuHarness) -> None:
    search_window.evaluate("popup.contentItem.children[0].text = 'kde'")
    QTest.qWait(SETTLE_MILLISECONDS)

    assert search_window.evaluate("popup.opened") is True


def test_highlights_the_selected_row(search_window: MainMenuHarness) -> None:
    script = "popup.contentItem.children[1].itemAtIndex(0).children[1].highlighted"

    assert search_window.evaluate(script) is True
