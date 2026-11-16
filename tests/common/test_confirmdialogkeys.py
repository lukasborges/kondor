from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import Kondor
import "file:%s/qml/common"
ApplicationWindow {
    visible: true
    width: 600; height: 400
    property bool wasAccepted: false
    ConfirmDialog {
        objectName: "dialog"; message: "Sure?"; acceptText: "Fill"
        onAccepted: wasAccepted = true
    }
}
"""


def open_dialog(qtbot: QtBot, engine: QQmlEngine) -> tuple[QObject, QObject, QQmlComponent]:
    root = Path(__file__).resolve().parents[2]
    component = load_component(engine, WINDOW_QML % root)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    qtbot.waitExposed(window)
    dialog = window.findChild(QObject, "dialog")
    dialog.open()
    qtbot.waitUntil(lambda: bool(dialog.property("opened")))
    return window, dialog, component


def test_enter_right_after_opening_rejects(qtbot: QtBot, kondor_engine: QQmlEngine) -> None:
    window, dialog, component = open_dialog(qtbot, kondor_engine)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: not dialog.property("opened"))
    assert not window.property("wasAccepted")


def test_cancel_shows_a_focus_frame_when_opened(qtbot: QtBot, kondor_engine: QQmlEngine) -> None:
    window, dialog, component = open_dialog(qtbot, kondor_engine)
    cancel = window.findChild(QObject, "cancelButton")
    assert cancel.property("visualFocus")


def test_enter_on_the_accept_button_accepts(qtbot: QtBot, kondor_engine: QQmlEngine) -> None:
    window, dialog, component = open_dialog(qtbot, kondor_engine)
    window.findChild(QObject, "acceptButton").forceActiveFocus()
    QTest.keyClick(window, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: bool(window.property("wasAccepted")))
