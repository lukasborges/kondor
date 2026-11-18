import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest

from tests.app.menu.mainmenuharness import QML_APP_DIRECTORY, MainMenuHarness

pytestmark = pytest.mark.no_qt_log

SHORTCUTS_WINDOW_QML = """
import QtQuick
import QtQuick.Controls
import Kondor
import "file://%s"

ApplicationWindow {
    id: window
    width: 300
    height: 200
    property int normalReloads: 0
    property int bypassReloads: 0
    TabModel { id: tabs }
    BrowserShortcuts {
        tabs: tabs
        browserWindow: window
        tabController: null
        dialogs: null
        navigationBar: null
        pageArea: null
        fullScreen: null
        tabSearch: QtObject { property bool opened: false; function show() {} }
    }
    Connections {
        target: tabs.currentTab
        function onReloadRequested() { window.normalReloads++ }
        function onReloadBypassingCacheRequested() { window.bypassReloads++ }
    }
}
"""
CONTROL = Qt.KeyboardModifier.ControlModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier
NONE = Qt.KeyboardModifier.NoModifier


@pytest.fixture
def shortcuts_window(kondor_engine: QQmlEngine) -> MainMenuHarness:
    source = SHORTCUTS_WINDOW_QML % QML_APP_DIRECTORY
    harness = MainMenuHarness(kondor_engine, source)
    harness.show()
    return harness


@pytest.mark.parametrize(
    ("key", "modifiers"),
    [
        (Qt.Key.Key_R, CONTROL | SHIFT),
        (Qt.Key.Key_F5, SHIFT),
        (Qt.Key.Key_F5, CONTROL),
    ],
)
def test_bypass_shortcuts_reload_without_the_cache(
    shortcuts_window: MainMenuHarness, key: Qt.Key, modifiers: Qt.KeyboardModifier
) -> None:
    shortcuts_window.tabs.currentTab.setUrl(QUrl("https://a.example"))
    QTest.keyClick(shortcuts_window.window, key, modifiers)

    assert shortcuts_window.window.property("bypassReloads") == 1
    assert shortcuts_window.window.property("normalReloads") == 0


def test_f5_still_does_a_normal_reload(shortcuts_window: MainMenuHarness) -> None:
    QTest.keyClick(shortcuts_window.window, Qt.Key.Key_F5, NONE)

    assert shortcuts_window.window.property("normalReloads") == 1
    assert shortcuts_window.window.property("bypassReloads") == 0
