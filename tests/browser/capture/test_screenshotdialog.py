from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """
import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    width: 600; height: 500
    visible: true
    ScreenshotDialog { id: dialog }
    function show() { dialog.openForTab(testTab) }
}
"""


@pytest.fixture
def tab(kondor_engine: QQmlEngine) -> Tab:
    return Tab(ProfileManager.instance().defaultProfile())


@pytest.fixture
def window(kondor_engine: QQmlEngine, tab: Tab) -> Iterator[QObject]:
    kondor_engine.rootContext().setContextProperty("testTab", tab)
    component: QQmlComponent = load_component(kondor_engine, WINDOW_QML)
    created = component.create()
    assert created is not None, error_text(component)
    yield created
    created.deleteLater()


def test_opening_asks_the_tab_for_the_visible_area(window: QObject, tab: Tab, qtbot: QtBot) -> None:
    with qtbot.waitSignal(tab.screenshotRequested, timeout=3000) as blocker:
        window.metaObject().invokeMethod(window, "show")
    assert blocker.args == [False]
