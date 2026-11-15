from collections.abc import Iterator

import pytest
from PySide6.QtCore import QSettings

from kondor.extensions.state.extensionstate import ExtensionState

EXTENSION = "state-test"


@pytest.fixture
def state(qapp: object) -> Iterator[ExtensionState]:
    extension_state = ExtensionState()
    extension_state.remove_extension(EXTENSION)
    yield extension_state
    extension_state.remove_extension(EXTENSION)
    extension_state.sync()


def test_defaults(state: ExtensionState) -> None:
    assert state.is_enabled(EXTENSION)
    assert not state.is_private_allowed(EXTENSION)
    assert state.source(EXTENSION) == "file"


def test_empty_disabled_sites_remove_the_key(state: ExtensionState) -> None:
    state.set_disabled_sites(EXTENSION, ["https://kde.org"])
    assert state.disabled_sites(EXTENSION) == ["https://kde.org"]
    state.set_disabled_sites(EXTENSION, [])
    state.sync()
    assert not QSettings("KDE", "Kondor").contains(f"Extensions/{EXTENSION}/DisabledSites")


def test_reads_values_written_by_qsettings_as_cpp_does(state: ExtensionState) -> None:
    written = QSettings("KDE", "Kondor")
    written.setValue(f"Extensions/{EXTENSION}/Enabled", "false")
    written.setValue(f"Extensions/{EXTENSION}/PrivateAllowed", "true")
    written.setValue(f"Extensions/{EXTENSION}/DisabledSites", ["https://kde.org"])
    written.sync()
    assert not state.is_enabled(EXTENSION)
    assert state.is_private_allowed(EXTENSION)
    assert state.disabled_sites(EXTENSION) == ["https://kde.org"]


def test_settings_live_under_their_key(state: ExtensionState) -> None:
    assert not state.has_setting(EXTENSION, "greeting")
    state.set_setting(EXTENSION, "greeting", "ola")
    assert state.has_setting(EXTENSION, "greeting")
    assert state.setting(EXTENSION, "greeting") == "ola"
