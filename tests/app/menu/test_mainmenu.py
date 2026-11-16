import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtTest import QTest

from tests.app.menu.mainmenuharness import (
    MainMenuHarness,
    expected_help_rows,
    expected_more_tools_rows,
    expected_top_level_rows,
    sequences_in,
    without_separators,
)
from tests.qmlsupport import captured_messages

pytestmark = pytest.mark.no_qt_log
HISTORY = "mainMenu.itemAt(7).subMenu"
SEPARATOR_COUNT = 5
ROW_COUNT = 14
MINIMUM_ACTIONS = 10


def test_rows_and_order(menu: MainMenuHarness) -> None:
    rows = menu.rows_of("mainMenu")

    assert rows == expected_top_level_rows()
    assert rows.count("-") == SEPARATOR_COUNT
    assert len(without_separators(rows)) == ROW_COUNT
    assert menu.rows_of("mainMenu.itemAt(15).subMenu") == expected_more_tools_rows()
    assert menu.rows_of("mainMenu.itemAt(18).subMenu") == expected_help_rows()


def test_history_submenu_lists_recently_closed_tabs(menu: MainMenuHarness) -> None:
    menu.evaluate(f"{HISTORY}.aboutToShow()")
    assert menu.rows_of(HISTORY) == ["Show All History", "Reopen Closed Tab"]

    menu.tabs.addTab(False, QUrl("https://b.example"))
    menu.tabs.addTab(False, QUrl("https://c.example"))
    menu.tabs.closeTab(1)
    menu.tabs.closeTab(1)
    menu.evaluate(f"{HISTORY}.aboutToShow()")

    rows = menu.rows_of(HISTORY)
    expected = ["Show All History", "Reopen Closed Tab", "-", "Recently Closed Tabs"]
    assert rows[:4] == expected
    assert rows[4:6] == ["https://c.example", "https://b.example"]


def test_shortcuts_work_with_the_menu_closed(menu: MainMenuHarness) -> None:
    with captured_messages() as warnings:
        QTest.keyClick(menu.window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
        assert menu.window.property("newTabs") == 1
        menu.tabs.addTab(False, QUrl("https://b.example"))
        menu.tabs.closeTab(1)
        assert menu.tabs.canReopenClosedTab
        reopen = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        QTest.keyClick(menu.window, Qt.Key.Key_T, reopen)

    assert menu.window.property("reopens") == 1
    assert menu.tabs.count == 2  # noqa: PLR2004
    assert not [warning for warning in warnings if "Ambiguous" in warning]


def test_actions_do_not_share_a_sequence_with_a_shortcut() -> None:
    actions = sequences_in("BrowserActions.qml", r'shortcut: ("[^"]+"|StandardKey\.\w+)')
    shortcuts = sequences_in("BrowserShortcuts.qml", r"Shortcut \{\s*sequences?: ([^\n]+)")

    assert len(actions) >= MINIMUM_ACTIONS
    assert shortcuts
    shared = [a for a in actions for s in shortcuts if a in s]
    assert shared == []


def test_opening_the_menu_highlights_no_item(menu: MainMenuHarness) -> None:
    menu.evaluate("mainMenu.open()")
    assert menu.wait_until_opened()

    assert menu.evaluate("mainMenu.currentIndex") == -1

    QTest.keyClick(menu.window, Qt.Key.Key_Down)
    assert menu.evaluate("mainMenu.currentIndex") == 0


def test_down_skips_separators_and_disabled_items(menu: MainMenuHarness) -> None:
    menu.evaluate("mainMenu.open()")
    assert menu.wait_until_opened()

    for _ in range(6):
        QTest.keyClick(menu.window, Qt.Key.Key_Down)

    assert menu.evaluate("mainMenu.itemAt(mainMenu.currentIndex).text") == "Bookmarks"
