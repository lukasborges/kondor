import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.extensions.panel.panelitems import click_center_of
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor
ApplicationWindow {
    visible: true
    width: 600; height: 400
    %s { id: popup; objectName: "popup"; x: 300; y: 20 }
    ToolButton {
        objectName: "opener"; focusPolicy: Qt.TabFocus; text: "Open"
        onClicked: popup.open()
    }
    TextField { objectName: "address"; y: 100; width: 200 }
    TextField { objectName: "other"; y: 150; width: 200 }
    WebEngineView { y: 200; width: 500; height: 150 }
}
"""
POPUPS = ["SiteInfoPopup", "AdBlockPopup", "DownloadsPopup"]


def open_popup_window(
    qtbot: QtBot, engine: QQmlEngine, popup_type: str
) -> tuple[QObject, QObject, QQmlComponent]:
    component = load_component(engine, WINDOW_QML % popup_type)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    qtbot.waitExposed(window)
    return window, window.findChild(QObject, "popup"), component


def open_with_click(qtbot: QtBot, window: QObject, popup: QObject) -> None:
    click_center_of(window.findChild(QObject, "opener"))
    qtbot.waitUntil(lambda: bool(popup.property("opened")))


def close_window(window: QObject, component: QQmlComponent) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()


@pytest.mark.parametrize("popup_type", POPUPS)
def test_escape_closes_the_popup(qtbot: QtBot, kondor_engine: QQmlEngine, popup_type: str) -> None:
    window, popup, component = open_popup_window(qtbot, kondor_engine, popup_type)
    open_with_click(qtbot, window, popup)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not popup.property("opened"))
    close_window(window, component)


@pytest.mark.parametrize("popup_type", POPUPS)
def test_escape_gives_focus_back_to_the_field_that_had_it(
    qtbot: QtBot, kondor_engine: QQmlEngine, popup_type: str
) -> None:
    window, popup, component = open_popup_window(qtbot, kondor_engine, popup_type)
    address = window.findChild(QObject, "address")
    address.forceActiveFocus()
    open_with_click(qtbot, window, popup)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: bool(address.property("activeFocus")))
    close_window(window, component)


@pytest.mark.parametrize("popup_type", POPUPS)
def test_clicking_another_field_keeps_focus_there(
    qtbot: QtBot, kondor_engine: QQmlEngine, popup_type: str
) -> None:
    window, popup, component = open_popup_window(qtbot, kondor_engine, popup_type)
    window.findChild(QObject, "address").forceActiveFocus()
    open_with_click(qtbot, window, popup)
    other = window.findChild(QObject, "other")
    click_center_of(other)
    qtbot.waitUntil(lambda: not popup.property("opened"))
    assert other.property("activeFocus")
    close_window(window, component)
