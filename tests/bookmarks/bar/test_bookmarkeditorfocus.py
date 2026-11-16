from collections.abc import Iterator

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from tests.bookmarks.bookmarkrows import add_page, manager
from tests.qmlsupport import error_text, load_component

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    visible: true
    width: 600; height: 400
    property int bookmarkId: 0
    BookmarkEditorPopup {
        id: popup; objectName: "popup"; parent: Overlay.overlay
        tabs: null
    }
    Shortcut { sequence: "Ctrl+D"; onActivated: popup.edit(bookmarkId, true) }
}
"""


@pytest.fixture
def window(
    fresh_bookmarks: object, kondor_engine: QQmlEngine, qtbot: QtBot
) -> Iterator[QQuickWindow]:
    component: QQmlComponent = load_component(kondor_engine, WINDOW_QML)
    created = component.create()
    assert created is not None, error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    created.setProperty("bookmarkId", add_page(manager().toolbarFolderId(), "Page", "page"))
    qtbot.waitExposed(created)
    yield created
    created.close()
    created.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def popup_of(window: QQuickWindow) -> QObject:
    return window.findChild(QObject, "popup")


def test_escape_closes_the_popup_opened_with_ctrl_d(window: QQuickWindow, qtbot: QtBot) -> None:
    qtbot.keyClick(window, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: bool(popup_of(window).property("opened")))
    qtbot.keyClick(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not popup_of(window).property("visible"))
