from PySide6.QtCore import Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.passwords.itemfinder import ItemFinder
from tests.passwords.panel.popupsupport import (
    OTHER_SITE,
    call,
    click_center_of,
    loaded_window,
    popup_qml,
    type_text,
)

RESULT_ROW = "savedLoginResultRow"
SEARCH_FIELD = "passwordSearchField"
NO_PASSWORDS_TEXT = "No Passwords for This Site"
EXAMPLE_MATCH_COUNT = 3


def search_field(window: QQuickWindow, finder: ItemFinder) -> object:
    return finder.popup_items(window, SEARCH_FIELD)[0]


def result_count(window: QQuickWindow, finder: ItemFinder) -> int:
    return len(finder.popup_items(window, RESULT_ROW))


def test_typing_filters_every_sites_logins(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    type_text(popup_window, "EXAMPLE")
    qtbot.waitUntil(lambda: result_count(popup_window, finder) == EXAMPLE_MATCH_COUNT)


def test_other_site_row_opens_the_confirmation(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    type_text(popup_window, "carol")
    qtbot.waitUntil(lambda: len(finder.popup_items(popup_window, RESULT_ROW)) == 1)
    QTest.keyClick(popup_window, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: popup_window.property("askedUsername") == "carol")
    assert not finder.is_popup_opened(popup_window)
    assert popup_window.property("filledLogin") == ""


def ask_to_fill(window: QQuickWindow, qtbot: QtBot) -> None:
    login = {"origin": OTHER_SITE, "host": "id.example.net", "username": "carol"}
    call(window, "askToFill", login)
    qtbot.waitUntil(lambda: window.property("isDialogOpened"))


def test_cancel_does_not_fill(popup_window: QQuickWindow, qtbot: QtBot) -> None:
    ask_to_fill(popup_window, qtbot)
    call(popup_window, "rejectDialog")
    qtbot.waitUntil(lambda: popup_window.property("isPageFocused"))
    assert popup_window.property("filledLogin") == ""


def test_fill_in_the_confirmation_fills(popup_window: QQuickWindow, qtbot: QtBot) -> None:
    ask_to_fill(popup_window, qtbot)
    call(popup_window, "acceptDialog")
    qtbot.waitUntil(lambda: popup_window.property("filledLogin") == f"{OTHER_SITE}|carol")


def test_escape_clears_the_text_then_closes(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    type_text(popup_window, "zzz")
    QTest.keyClick(popup_window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: search_field(popup_window, finder).property("text") == "")
    assert finder.is_popup_opened(popup_window)
    QTest.keyClick(popup_window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not finder.is_popup_opened(popup_window))


def test_site_without_logins_shows_the_empty_state(
    kondor_engine: QQmlEngine, finder: ItemFinder, qtbot: QtBot
) -> None:
    with loaded_window(kondor_engine, popup_qml([])) as window:
        finder.open_popup(window)
        qtbot.waitUntil(lambda: finder.is_popup_opened(window))
        qtbot.waitUntil(lambda: finder.popup_text(window, NO_PASSWORDS_TEXT) is not None)


def test_row_click_on_other_site_login_asks_first(
    popup_window: QQuickWindow, finder: ItemFinder, qtbot: QtBot
) -> None:
    type_text(popup_window, "carol")
    qtbot.waitUntil(lambda: len(finder.popup_items(popup_window, RESULT_ROW)) == 1)
    click_center_of(popup_window, finder.popup_items(popup_window, RESULT_ROW)[0])
    qtbot.waitUntil(lambda: popup_window.property("askedUsername") == "carol")
