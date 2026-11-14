import pytest
from pytestqt.qtbot import QtBot

from kondor.core.settings.settings import Settings
from kondor.passwords.passwordstore import PasswordStore
from pytests.settings.settingswindowharness import (
    CHANGED_OPTION_PER_PAGE,
    SettingsWindowHarness,
)

pytestmark = pytest.mark.no_qt_log
PAGE_TITLES = ["general", "search", "downloads", "privacy", "passwords", "extensions", "spelling"]
PASSWORDS_PAGE = 4


def search_engine() -> object:
    return Settings.instance().property("searchEngine")


def test_pending_changes_are_discarded(settings_window: SettingsWindowHarness) -> None:
    settings_window.show_window()
    assert settings_window.window.isVisible()
    pending = settings_window.pending()
    assert not settings_window.is_modified()
    pending.setProperty("searchEngine", "google")
    assert settings_window.is_modified()
    assert search_engine() == "duckduckgo"

    settings_window.invoke("discardChanges")
    assert not settings_window.window.isVisible()
    assert search_engine() == "duckduckgo"
    settings_window.show_window()

    assert pending.property("searchEngine") == "duckduckgo"
    assert not settings_window.is_modified()


def test_apply_writes_and_disables_apply(settings_window: SettingsWindowHarness) -> None:
    settings_window.show_window()
    settings_window.pending().setProperty("searchEngine", "google")

    settings_window.invoke("applyChanges")

    assert search_engine() == "google"
    assert not settings_window.is_modified()


def test_ok_applies_and_closes(settings_window: SettingsWindowHarness) -> None:
    settings_window.show_window()
    settings_window.pending().setProperty("customSearchUrl", "https://example.com/?q=%1")

    settings_window.invoke("acceptAndClose")

    assert not settings_window.window.isVisible()
    assert Settings.instance().property("customSearchUrl") == "https://example.com/?q=%1"


@pytest.mark.parametrize("page", range(len(PAGE_TITLES)), ids=PAGE_TITLES)
def test_every_page_defaults_reset_only_its_options(
    settings_window: SettingsWindowHarness, page: int
) -> None:
    settings_window.show_window()
    draft = settings_window.pending()
    for name, value in CHANGED_OPTION_PER_PAGE:
        draft.setProperty(name, value)
    settings_window.window.setProperty("currentPage", page)
    assert settings_window.window.property("defaultsEnabled") is True

    settings_window.invoke("restoreDefaults")

    for index, (name, value) in enumerate(CHANGED_OPTION_PER_PAGE):
        expected = Settings.instance().defaultValue(name) if index == page else value
        assert draft.property(name) == expected
    assert settings_window.window.property("defaultsEnabled") is False


def test_wallet_unavailable_state(settings_window: SettingsWindowHarness, qtbot: QtBot) -> None:
    assert settings_window.show_exposed()
    settings_window.window.setProperty("currentPage", PASSWORDS_PAGE)

    qtbot.waitUntil(lambda: PasswordStore.instance().property("state") == "unavailable")
