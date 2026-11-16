from collections.abc import Iterator

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtQml import QQmlEngine
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
    WebEngineView { id: view; y: 50; width: 500; height: 300 }
    QtObject {
        id: browserActions
        property Action savePageAction: Action { enabled: false }
        property Action printAction: Action { enabled: false }
    }
    PageContextMenu {
        id: pageMenu; objectName: "pageMenu"
        webView: view; browserActions: browserActions
    }
    function showPageMenu() { pageMenu.popupAt(Qt.point(10, 10)) }
    property string currentText: {
        const item = pageMenu.currentIndex < 0 ? null : pageMenu.itemAt(pageMenu.currentIndex)
        return item ? item.text : ""
    }
}
"""


@pytest.fixture
def window(kondor_engine: QQmlEngine, qtbot: QtBot) -> Iterator[QQuickWindow]:
    Settings.instance().setProperty("spellCheckEnabled", False)
    component = load_component(kondor_engine, WINDOW_QML)
    created = component.create()
    assert created is not None, error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    qtbot.waitExposed(created)
    yield created
    created.close()
    created.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def open_page_menu(window: QQuickWindow, qtbot: QtBot) -> None:
    menu = window.findChild(QObject, "pageMenu")
    assert menu is not None
    window.metaObject().invokeMethod(window, "showPageMenu")
    qtbot.waitUntil(lambda: bool(menu.property("opened")))


def press_down(window: QQuickWindow, qtbot: QtBot, times: int = 1) -> str:
    for _ in range(times):
        qtbot.keyClick(window, Qt.Key.Key_Down)
    return str(window.property("currentText"))


def test_first_down_press_highlights_reload_when_back_and_forward_are_disabled(
    window: QQuickWindow, qtbot: QtBot
) -> None:
    open_page_menu(window, qtbot)
    assert press_down(window, qtbot) == "Reload"


def test_down_skips_separator_and_disabled_items(window: QQuickWindow, qtbot: QtBot) -> None:
    open_page_menu(window, qtbot)
    press_down(window, qtbot)
    assert press_down(window, qtbot) == "View Page Source"


def test_down_wraps_to_first_enabled_item(window: QQuickWindow, qtbot: QtBot) -> None:
    open_page_menu(window, qtbot)
    assert press_down(window, qtbot, 3) == "Inspect Element"
    assert press_down(window, qtbot) == "Reload"


def test_up_from_no_current_item_highlights_last_item(window: QQuickWindow, qtbot: QtBot) -> None:
    open_page_menu(window, qtbot)
    qtbot.keyClick(window, Qt.Key.Key_Up)
    assert window.property("currentText") == "Inspect Element"


def test_up_skips_separator_and_disabled_items(window: QQuickWindow, qtbot: QtBot) -> None:
    open_page_menu(window, qtbot)
    press_down(window, qtbot, 2)
    qtbot.keyClick(window, Qt.Key.Key_Up)
    assert window.property("currentText") == "Reload"
