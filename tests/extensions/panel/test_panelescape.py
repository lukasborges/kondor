from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.extensions.panel import toolbarharness as harness
from tests.extensions.panel.panelitems import click_center_of
from tests.extensions.panel.toolbarharness import ToolBar

pytestmark = pytest.mark.no_qt_log

WEB_WINDOW_QML = """import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor
ApplicationWindow {
    visible: true
    width: 700; height: 400
    ExtensionsToolButtons { tabs: theTabs; browserWindow: null }
    TextField { id: address; objectName: "address"; x: 300; width: 300 }
    WebEngineView {
        y: 50; width: 600; height: 300; focus: true
        Component.onCompleted: forceActiveFocus()
    }
}
"""


@pytest.fixture(autouse=True)
def web_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(harness, "TOOL_BAR_QML", WEB_WINDOW_QML)


@pytest.fixture
def toolbar(qtbot: QtBot, work: str, kondor_engine: QQmlEngine) -> Iterator[ToolBar]:
    tool_bar = ToolBar(qtbot, kondor_engine, work)
    tool_bar.show()
    yield tool_bar
    tool_bar.close()


def open_with_click(toolbar: ToolBar) -> QObject:
    click_center_of(toolbar.named("extensionsButton"))
    panel = toolbar.window.findChild(QObject, "extensionsPanel")
    toolbar.qtbot.waitUntil(lambda: bool(panel.property("opened")))
    return panel


def test_escape_closes_the_panel_opened_with_the_mouse(toolbar: ToolBar) -> None:
    panel = open_with_click(toolbar)
    QTest.keyClick(toolbar.window, Qt.Key.Key_Escape)
    toolbar.qtbot.waitUntil(lambda: not panel.property("opened"))


def test_click_on_another_field_keeps_focus_there_after_the_panel_closes(toolbar: ToolBar) -> None:
    panel = open_with_click(toolbar)
    address = toolbar.named("address")
    click_center_of(address)
    toolbar.qtbot.waitUntil(lambda: not panel.property("opened"))
    assert address.hasActiveFocus()


def test_clicking_the_button_again_closes_the_panel(toolbar: ToolBar) -> None:
    panel = open_with_click(toolbar)
    click_center_of(toolbar.named("extensionsButton"))
    toolbar.qtbot.waitUntil(lambda: not panel.property("opened"))
    toolbar.qtbot.wait(100)
    assert not panel.property("opened")


def test_escape_closes_the_panel_inside_an_extension_page(toolbar: ToolBar) -> None:
    panel = open_with_click(toolbar)
    panel.setProperty("currentId", "sample")
    toolbar.qtbot.wait(100)
    QTest.keyClick(toolbar.window, Qt.Key.Key_Escape)
    toolbar.qtbot.waitUntil(lambda: not panel.property("opened"))


def test_tab_reaches_the_extensions_button_and_space_opens_the_panel(toolbar: ToolBar) -> None:
    button = toolbar.named("extensionsButton")
    assert button.property("focusPolicy") == Qt.FocusPolicy.TabFocus
    button.forceActiveFocus(Qt.FocusReason.TabFocusReason)
    QTest.keyClick(toolbar.window, Qt.Key.Key_Space)
    panel = toolbar.window.findChild(QObject, "extensionsPanel")
    toolbar.qtbot.waitUntil(lambda: bool(panel.property("opened")))
