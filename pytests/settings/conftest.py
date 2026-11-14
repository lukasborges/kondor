from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine

from pytests.settings.settingswindowharness import (
    SettingsWindowHarness,
    reset_settings_to_test_defaults,
)


@pytest.fixture(autouse=True)
def default_settings(monkeypatch: pytest.MonkeyPatch, kondor_types: None) -> None:
    monkeypatch.setenv("KONDOR_NO_KWALLET", "1")
    reset_settings_to_test_defaults()


@pytest.fixture
def settings_window(
    kondor_engine: QQmlEngine, desktop_style: None
) -> Iterator[SettingsWindowHarness]:
    harness = SettingsWindowHarness(kondor_engine)
    yield harness
    harness.close()
