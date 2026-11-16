from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow

from tests.settings.settingsshortcutshost import ShortcutsHost
from tests.settings.settingswindowharness import SettingsWindowHarness

pytestmark = pytest.mark.no_qt_log


def window_shortcuts(window: QQuickWindow) -> list[QObject]:
    return [
        child
        for child in window.findChildren(QObject)
        if child.metaObject().className().startswith("WindowShortcut")
    ]


def test_hidden_settings_window_has_no_active_shortcuts(
    settings_window: SettingsWindowHarness,
) -> None:
    shortcuts = window_shortcuts(settings_window.window)
    assert shortcuts
    assert not any(shortcut.property("enabled") for shortcut in shortcuts)


def test_closed_settings_window_has_no_active_shortcuts(
    settings_window: SettingsWindowHarness,
) -> None:
    assert settings_window.show_exposed()
    settings_window.window.close()
    shortcuts = window_shortcuts(settings_window.window)
    assert not any(shortcut.property("enabled") for shortcut in shortcuts)


@pytest.fixture
def shortcuts_host(kondor_engine: QQmlEngine, desktop_style: None) -> Iterator[ShortcutsHost]:
    host = ShortcutsHost(kondor_engine)
    yield host
    host.close()


def test_find_works_in_browser_window_after_settings_closed(
    shortcuts_host: ShortcutsHost,
) -> None:
    shortcuts_host.open_settings()
    shortcuts_host.settings().close()
    shortcuts_host.focus_page_field()
    shortcuts_host.press_find(shortcuts_host.window)
    assert shortcuts_host.find_count() == 1


@pytest.mark.xfail(
    strict=False,
    reason="passes alone; offscreen delivers no shortcut to a second host window in one process",
)
def test_find_works_in_browser_window_while_settings_is_open_but_unfocused(
    shortcuts_host: ShortcutsHost,
) -> None:
    shortcuts_host.open_settings()
    shortcuts_host.focus_page_field()
    shortcuts_host.press_find(shortcuts_host.window)
    assert shortcuts_host.find_count() == 1


def test_find_in_focused_settings_window_does_not_reach_the_browser(
    shortcuts_host: ShortcutsHost,
) -> None:
    shortcuts_host.open_settings()
    shortcuts_host.focus_settings()
    shortcuts_host.press_find(shortcuts_host.settings())
    assert shortcuts_host.find_count() == 0


@pytest.mark.xfail(strict=False, reason="offscreen does not deliver this shortcut")
def test_find_in_focused_settings_window_activates_its_own_shortcut(
    shortcuts_host: ShortcutsHost,
) -> None:
    shortcuts_host.open_settings()
    activations = shortcuts_host.count_settings_find_activations()
    shortcuts_host.focus_settings()
    shortcuts_host.press_find(shortcuts_host.settings())
    assert activations == [1]
