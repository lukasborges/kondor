import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor
ApplicationWindow {
    visible: true
    width: 300; height: 200
    property color schemeBlue: Kirigami.Theme.highlightColor
    Popup {
        id: popup
        objectName: "popup"
        GroupSwatch { objectName: "swatch"; colorName: "blue" }
    }
}
"""


def test_swatch_inside_a_popup_shows_the_scheme_color(
    qtbot: QtBot, kondor_engine: QQmlEngine, desktop_style: None
) -> None:
    component = load_component(kondor_engine, WINDOW_QML)
    window = component.create()
    assert window is not None, error_text(component)
    popup = window.findChild(QObject, "popup")
    popup.open()
    qtbot.waitUntil(lambda: bool(popup.property("opened")))
    swatch = window.findChild(QObject, "swatch")
    shown: QColor = swatch.property("contentItem").property("color")
    assert shown == window.property("schemeBlue")
    assert shown != QColor("black")
    window.close()
    window.deleteLater()
    component.deleteLater()
