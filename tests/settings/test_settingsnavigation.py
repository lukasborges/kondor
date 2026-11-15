import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.settings.settingsnavigationharness import (
    ALL_PAGES,
    PAGE_TITLES,
    Page,
    click_sidebar_entry_and_verify,
    focus_search_field,
    search_for,
    verify_only_page_is_listed,
    verify_privacy_is_the_only_entry,
    verify_shown_page,
    visible_page_count,
)
from tests.settings.settingswindowharness import SettingsWindowHarness

pytestmark = pytest.mark.no_qt_log
PASSWORDS_PAGE = 4


def test_clicking_sidebar_switches_pages(
    settings_window: SettingsWindowHarness, qtbot: QtBot
) -> None:
    assert settings_window.show_exposed()
    verify_shown_page(settings_window, 0, PAGE_TITLES[0])
    for page, title in enumerate(PAGE_TITLES):
        click_sidebar_entry_and_verify(settings_window, qtbot, Page(page, title))

    settings_window.invoke("discardChanges")

    assert settings_window.show_exposed()
    verify_shown_page(settings_window, 3, PAGE_TITLES[3])


def test_arrow_keys_move_between_pages(settings_window: SettingsWindowHarness) -> None:
    window = settings_window.window
    assert settings_window.show_exposed()
    verify_shown_page(settings_window, 0, "General")
    for key, page, title in [
        (Qt.Key.Key_Down, 1, "Search"),
        (Qt.Key.Key_Down, 2, "Downloads"),
        (Qt.Key.Key_Up, 1, "Search"),
    ]:
        QTest.keyClick(window, key)
        verify_shown_page(settings_window, page, title)

    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert not window.isVisible()


def test_search_filters_pages(settings_window: SettingsWindowHarness, qtbot: QtBot) -> None:
    assert settings_window.show_exposed()
    assert visible_page_count(settings_window) == ALL_PAGES
    assert focus_search_field(settings_window)

    search_for(settings_window, "cookies")
    verify_privacy_is_the_only_entry(settings_window, qtbot)
    search_for(settings_window, "engine")
    verify_only_page_is_listed(settings_window, qtbot, Page(1, "Search"))
    search_for(settings_window, "kwallet")
    verify_only_page_is_listed(settings_window, qtbot, Page(PASSWORDS_PAGE, "Passwords"))
    search_for(settings_window, "")

    qtbot.waitUntil(lambda: visible_page_count(settings_window) == ALL_PAGES)
    verify_shown_page(settings_window, PASSWORDS_PAGE, "Passwords")
