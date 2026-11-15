from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtTest import QSignalSpy

from kondor.core.settings.settings import Settings
from kondor.extensions.extensionmanager import ExtensionManager
from tests.extensions import extensionsharness as harness


@pytest.fixture(autouse=True)
def clean_manager(qapp: object) -> Iterator[None]:
    yield
    harness.remove_every_extension()


def ids_of(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["id"] for entry in entries]


def test_pinned_extensions_keep_pin_order(tmp_path: Path) -> None:
    assert harness.install_named(str(tmp_path), "alpha", "Alpha")
    assert harness.install_named(str(tmp_path), "beta", "Beta")
    manager = ExtensionManager.instance()
    manager.setPinned("beta", True)
    manager.setPinned("alpha", True)
    assert ids_of(manager.pinnedActionExtensions(False)) == ["beta", "alpha"]


def test_set_pinned_ignores_duplicates() -> None:
    manager = ExtensionManager.instance()
    changes = QSignalSpy(Settings.instance().pinnedExtensionsChanged)
    manager.setPinned("sample", True)
    manager.setPinned("sample", True)
    assert changes.count() == 1
    assert Settings.instance().pinnedExtensions == ["sample"]


def test_remove_unpins_extension(tmp_path: Path) -> None:
    assert harness.install_sample(str(tmp_path))
    manager = ExtensionManager.instance()
    manager.setPinned("sample", True)
    assert manager.isPinned("sample")
    manager.remove("sample")
    assert not manager.isPinned("sample")


def test_pinned_hides_extensions_not_allowed_in_private(tmp_path: Path) -> None:
    assert harness.install_sample(str(tmp_path))
    manager = ExtensionManager.instance()
    manager.setPinned("sample", True)
    assert len(manager.pinnedActionExtensions(True)) == 0
    harness.allow_in_private_windows("sample")
    assert len(manager.pinnedActionExtensions(True)) == 1


def test_action_extensions_are_sorted_by_name(tmp_path: Path) -> None:
    assert harness.install_named(str(tmp_path), "zulu", "Zulu")
    assert harness.install_named(str(tmp_path), "alpha", "Alpha")
    assert ids_of(ExtensionManager.instance().actionExtensions(False)) == ["alpha", "zulu"]
