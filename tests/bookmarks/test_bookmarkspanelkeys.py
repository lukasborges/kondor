from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.favicons.faviconimageprovider import FaviconImageProvider
from tests.bookmarks.bookmarkrows import add_page, manager
from tests.qmlsupport import error_text, load_component

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    id: window
    visible: true
    width: 600; height: 600
    property var opened: []
    QtObject {
        id: fakeBrowserWindow
        function openUrl(url, background) { window.opened = window.opened.concat([url.toString()]) }
        function openBookmarks() {}
    }
    BookmarksPanel {
        id: panel; objectName: "panel"; parent: Overlay.overlay
        tab: null; browserWindow: fakeBrowserWindow
    }
}
"""
OTHER_PAGE = "other"


class PanelDriver:
    def __init__(self, qtbot: QtBot, window: QQuickWindow) -> None:
        self.qtbot = qtbot
        self.window = window
        self.panel = window.findChild(QObject, "panel")

    def open(self) -> None:
        self.panel.open()
        self.qtbot.waitUntil(lambda: bool(self.panel.property("opened")))

    def press(self, key: Qt.Key) -> None:
        self.qtbot.keyClick(self.window, key)

    def folder_depth(self) -> int:
        return len(self.panel.property("folderPath").toVariant())

    def opened_urls(self) -> list[str]:
        return list(self.window.property("opened").toVariant())


@pytest.fixture
def driver(fresh_bookmarks: Path, kondor_engine: QQmlEngine, qtbot: QtBot) -> Iterator[PanelDriver]:
    add_page(manager().otherFolderId(), "Other page", OTHER_PAGE)
    kondor_engine.addImageProvider("kondor-favicon", FaviconImageProvider())
    component: QQmlComponent = load_component(kondor_engine, WINDOW_QML)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    yield PanelDriver(qtbot, window)
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def enter_other_bookmarks(driver: PanelDriver) -> None:
    driver.open()
    driver.press(Qt.Key.Key_Down)
    for _ in range(6):
        driver.press(Qt.Key.Key_Down)
    driver.press(Qt.Key.Key_Right)


def test_right_enters_a_folder_and_enter_opens_its_first_bookmark(driver: PanelDriver) -> None:
    enter_other_bookmarks(driver)
    driver.qtbot.waitUntil(lambda: driver.folder_depth() == 1)
    driver.press(Qt.Key.Key_Return)
    assert driver.opened_urls() != []


def test_left_returns_from_a_folder_to_the_overview(driver: PanelDriver) -> None:
    enter_other_bookmarks(driver)
    driver.qtbot.waitUntil(lambda: driver.folder_depth() == 1)
    driver.press(Qt.Key.Key_Left)
    assert driver.folder_depth() == 0
