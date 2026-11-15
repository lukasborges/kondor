from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.passwords.itemfinder import ItemFinder
from tests.qmlsupport import error_text, load_component

EMPTY_SAVED_PASSWORDS_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    id: window
    visible: true
    width: 700; height: 400
    property bool isAddRequested: false
    SavedPasswordsList {
        anchors.fill: parent
        walletDenied: false
        filter: ""
        revealed: RevealedPasswords {}
        onAddRequested: window.isAddRequested = true
    }
}
"""
SAVED_PASSWORDS_POPUP_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    id: window
    visible: true
    width: 500; height: 400
    property string filledUsername: ""
    property bool isPageFocused: false
    property alias popup: popup
    QtObject {
        id: stubTab
        function focusPage() { window.isPageFocused = true }
        property QtObject passwords: QtObject {
            property var usernames: ["ana", "bruno"]
            property string host: "example.org"
            function fill(username) { window.filledUsername = username }
            function copyUsername(username) {}
            function copyPassword(username) {}
        }
    }
    SavedPasswordsPopup {
        id: popup
        parent: Overlay.overlay
        tab: stubTab
    }
}
"""
ADD_PASSWORD_TEXT = "Add Password…"
ROW_COUNT = 2
def click_center_of(window: QQuickWindow, item: QQuickItem) -> None:
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    button, modifiers = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    QTest.mouseClick(window, button, modifiers, center)


@contextmanager
def loaded_window(engine: QQmlEngine, source: str) -> Iterator[QQuickWindow]:
    component = load_component(engine, source)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    yield window
    window.close()


@pytest.fixture
def finder(kondor_engine: QQmlEngine) -> ItemFinder:
    return ItemFinder(kondor_engine)


@pytest.fixture
def popup_window(
    kondor_engine: QQmlEngine, finder: ItemFinder, qtbot: QtBot
) -> Iterator[QQuickWindow]:
    with loaded_window(kondor_engine, SAVED_PASSWORDS_POPUP_QML) as window:
        finder.open_popup(window)
        qtbot.waitUntil(lambda: len(finder.popup_rows(window)) == ROW_COUNT)
        qtbot.waitUntil(lambda: finder.is_popup_opened(window))
        yield window


def test_empty_list_button_requests_add(
    kondor_engine: QQmlEngine, finder: ItemFinder, qtbot: QtBot
) -> None:
    with loaded_window(kondor_engine, EMPTY_SAVED_PASSWORDS_QML) as window:
        saved_list = finder.named(window.contentItem(), "savedPasswordsList")[0]
        frame = saved_list.parentItem()
        qtbot.waitUntil(lambda: finder.with_text(frame, ADD_PASSWORD_TEXT) is not None)
        click_center_of(window, finder.with_text(frame, ADD_PASSWORD_TEXT))
        qtbot.waitUntil(lambda: window.property("isAddRequested"))


def test_row_click_fills_and_closes(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    second_row = finder.popup_rows(popup_window)[1]
    click_center_of(popup_window, second_row.childItems()[0])
    qtbot.waitUntil(lambda: popup_window.property("filledUsername") == "bruno")
    qtbot.waitUntil(lambda: not finder.is_popup_opened(popup_window))


def test_copy_button_shows_check_mark_and_stays_open(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    first_row = finder.popup_rows(popup_window)[0]
    buttons = finder.named(first_row, "copyPasswordButton")
    assert buttons
    buttons[0].click()
    qtbot.waitUntil(lambda: buttons[0].property("isCopied"))
    assert finder.is_popup_opened(popup_window)


def test_down_key_moves_to_next_row(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    rows = finder.popup_rows(popup_window)
    qtbot.waitUntil(rows[0].hasActiveFocus)
    QTest.keyClick(popup_window, Qt.Key.Key_Down)
    qtbot.waitUntil(rows[1].hasActiveFocus)


def test_escape_closes_and_focuses_page(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    rows = finder.popup_rows(popup_window)
    qtbot.waitUntil(rows[0].hasActiveFocus)
    QTest.keyClick(popup_window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not finder.is_popup_opened(popup_window))
    assert popup_window.property("isPageFocused")
