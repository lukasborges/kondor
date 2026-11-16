import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlEngine
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
    %s { id: popup; objectName: "popup"; x: 50; y: 50 }
    Button { objectName: "opener"; text: "Open"; onClicked: popup.open() }
    WebEngineView {
        y: 150; width: 500; height: 200; focus: true
        Component.onCompleted: forceActiveFocus()
    }
}
"""
POPUPS = ["SiteInfoPopup", "AdBlockPopup", "DownloadsPopup"]


@pytest.mark.parametrize("popup_type", POPUPS)
def test_escape_closes_the_popup_opened_without_focusing_it(
    qtbot: QtBot, kondor_engine: QQmlEngine, popup_type: str
) -> None:
    component = load_component(kondor_engine, WINDOW_QML % popup_type)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    popup = window.findChild(QObject, "popup")
    qtbot.waitExposed(window)
    click_center_of(window.findChild(QObject, "opener"))
    qtbot.waitUntil(lambda: bool(popup.property("opened")))
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not popup.property("opened"))
    window.close()
    window.deleteLater()
