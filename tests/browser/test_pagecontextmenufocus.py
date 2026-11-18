from collections.abc import Iterator

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.core.settings.settings import Settings
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

ApplicationWindow {
    visible: true
    width: 600; height: 400
    ToolButton {
        id: button; objectName: "button"; text: "Menu"; onClicked: mainMenu.open()
        Menu { id: mainMenu; objectName: "mainMenu"; MenuItem { text: "One" } }
    }
    WebEngineView { id: view; objectName: "view"; y: 50; width: 500; height: 300 }
    QtObject {
        id: browserActions
        property Action savePageAction: Action { enabled: true }
        property Action printAction: Action { enabled: true }
        property Action screenshotAction: Action { enabled: true }
    }
    PageContextMenu {
        id: pageMenu; objectName: "pageMenu"
        webView: view; browserActions: browserActions
    }
    function showPageMenu() { pageMenu.popupAt(Qt.point(10, 10)) }
}
"""


@pytest.fixture
def window(kondor_engine: QQmlEngine, qtbot: QtBot) -> Iterator[QQuickWindow]:
    Settings.instance().setProperty("spellCheckEnabled", False)
    component: QQmlComponent = load_component(kondor_engine, WINDOW_QML)
    created = component.create()
    assert created is not None, error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    qtbot.waitExposed(created)
    yield created
    created.close()
    created.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def child(window: QQuickWindow, name: str) -> QObject:
    found = window.findChild(QObject, name)
    assert found is not None
    return found


def open_and_close_main_menu(window: QQuickWindow, qtbot: QtBot) -> None:
    menu = child(window, "mainMenu")
    qtbot.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(20, 15))
    qtbot.waitUntil(lambda: bool(menu.property("opened")))
    qtbot.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not menu.property("visible"))


def test_page_menu_has_active_focus_after_main_menu_was_closed(
    window: QQuickWindow, qtbot: QtBot
) -> None:
    open_and_close_main_menu(window, qtbot)
    page_menu = child(window, "pageMenu")
    window.metaObject().invokeMethod(window, "showPageMenu")
    qtbot.waitUntil(lambda: bool(page_menu.property("opened")))
    assert page_menu.property("activeFocus")


def test_escape_closes_page_menu_after_main_menu_was_closed(
    window: QQuickWindow, qtbot: QtBot
) -> None:
    open_and_close_main_menu(window, qtbot)
    page_menu = child(window, "pageMenu")
    window.metaObject().invokeMethod(window, "showPageMenu")
    qtbot.waitUntil(lambda: bool(page_menu.property("opened")))
    qtbot.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not page_menu.property("visible"))


def test_page_gets_focus_back_when_page_menu_closes(window: QQuickWindow, qtbot: QtBot) -> None:
    open_and_close_main_menu(window, qtbot)
    page_menu = child(window, "pageMenu")
    window.metaObject().invokeMethod(window, "showPageMenu")
    qtbot.waitUntil(lambda: bool(page_menu.property("opened")))
    qtbot.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not page_menu.property("visible"))
    assert child(window, "view").property("activeFocus")
