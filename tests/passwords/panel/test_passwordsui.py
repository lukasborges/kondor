from PySide6.QtCore import Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.passwords.itemfinder import ItemFinder
from tests.passwords.panel.popupsupport import click_center_of, loaded_window

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
ADD_PASSWORD_TEXT = "Add Password…"


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
    qtbot.waitUntil(lambda: popup_window.property("filledLogin") == "https://example.org|bruno")
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


def test_copy_check_mark_uses_highlighted_text_color_on_current_row(
    popup_window: QQuickWindow, finder: ItemFinder
) -> None:
    rows = finder.popup_rows(popup_window)
    current = finder.named(rows[0], "copyPasswordButton")[0]
    other = finder.named(rows[1], "copyPasswordButton")[0]
    assert current.property("isOnHighlight")
    assert not other.property("isOnHighlight")
    assert current.property("checkColor") != other.property("checkColor")


def test_down_key_moves_to_next_row(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    rows = finder.popup_rows(popup_window)
    QTest.keyClick(popup_window, Qt.Key.Key_Down)
    qtbot.waitUntil(rows[0].hasActiveFocus)
    QTest.keyClick(popup_window, Qt.Key.Key_Down)
    qtbot.waitUntil(rows[1].hasActiveFocus)


def test_escape_closes_and_focuses_page(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    QTest.keyClick(popup_window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not finder.is_popup_opened(popup_window))
    assert popup_window.property("isPageFocused")
