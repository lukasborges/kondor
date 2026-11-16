import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickWindow

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
