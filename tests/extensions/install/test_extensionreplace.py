from pathlib import Path

from PySide6.QtCore import QModelIndex, QSettings
from PySide6.QtTest import QSignalSpy

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from kondor.extensions.state import extensionstorage
from tests.extensions.extensionsharness import (
    apply_settings,
    install_sample,
    pack_variant,
    sample_package,
)

Role = ExtensionManager.Role
DEFAULT_SIZE = 50
MAXIMUM_SIZE = 100


def manager() -> ExtensionManager:
    return ExtensionManager.instance()


def role_of(role: int) -> object:
    return manager().data(manager().index(0, 0, QModelIndex()), role)


def configure_sample_state() -> None:
    configuration = {
        "settings": {"greeting": "hi"},
        "privateAllowed": True,
        "disabledSites": ["https://example.com"],
    }
    manager().applyConfiguration("sample", configuration)
    manager().setEnabled("sample", False)
    assert extensionstorage.set_value("sample", "k", 1).is_written


def replace_sample_with_version_1_1(work: str) -> None:
    def edit(manifest: dict) -> None:
        manifest["version"] = "1.1.0"

    zip_path = pack_variant(work, "v11", edit)
    result = manager().install_package(PackageFile(zip_path, "catalog"), "sample")
    assert result.is_installed


def test_replace_keeps_state(work: str) -> None:
    assert install_sample(work)
    configure_sample_state()
    replace_sample_with_version_1_1(work)
    assert manager().installedVersion("sample") == "1.1.0"
    assert manager().source("sample") == "catalog"
    assert role_of(Role.EnabledRole) is False
    assert role_of(Role.PrivateAllowedRole) is True
    assert manager().settingValues("sample")["greeting"] == "hi"
    assert extensionstorage.value("sample", "k") == 1


def test_replace_leaves_no_temporary_folders(work: str) -> None:
    assert install_sample(work)
    replace_sample_with_version_1_1(work)
    directory = Path(manager().extensions_directory())
    assert not (directory / "sample.new").exists()
    assert not (directory / "sample.old").exists()


def test_package_for_another_id_is_refused(work: str) -> None:
    assert install_sample(work)
    file = PackageFile(sample_package(work), "catalog")
    error = manager().install_package(file, "other").error
    assert "not “other”" in error


def test_remove_deletes_everything(work: str) -> None:
    assert install_sample(work)
    apply_settings("sample", {"greeting": "bye"})
    assert extensionstorage.set_value("sample", "k", "v").is_written
    manager().remove("sample")
    assert not manager().isInstalled("sample")
    assert manager().count == 0
    assert not (Path(manager().extensions_directory()) / "sample").exists()
    assert extensionstorage.keys("sample") == []


def test_remove_forgets_the_stored_state(work: str) -> None:
    assert install_sample(work)
    apply_settings("sample", {"greeting": "bye"})
    manager().remove("sample")
    state = QSettings("KDE", "Kondor")
    state.beginGroup("Extensions")
    assert "sample" not in state.childGroups()
    state.endGroup()


def test_settings_are_sanitized(work: str) -> None:
    assert install_sample(work)
    assert manager().settingValues("sample")["size"] == DEFAULT_SIZE
    apply_settings(
        "sample", {"size": 500, "mode": "zzz", "enabledFeature": "nope", "greeting": "changed"}
    )
    values = manager().settingValues("sample")
    assert values["size"] == MAXIMUM_SIZE
    assert values["mode"] == "a"
    assert values["enabledFeature"] is True
    assert values["greeting"] == "changed"


def test_unchanged_settings_emit_nothing(work: str) -> None:
    assert install_sample(work)
    apply_settings("sample", {"greeting": "changed"})
    changed = QSignalSpy(manager().settingsChanged)
    apply_settings("sample", {"greeting": "changed"})
    assert changed.count() == 0
    apply_settings("sample", {"greeting": "again"})
    assert changed.count() == 1
    assert changed.at(0) == ["sample"]
