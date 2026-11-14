import zipfile
from pathlib import Path

from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QSignalSpy

from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import sample_package, write_file

Role = ExtensionManager.Role
PERMISSION_COUNT = 3
PREVIEW_PERMISSION = "Read and change pages on 127.0.0.1, localhost"


def manager() -> ExtensionManager:
    return ExtensionManager.instance()


def inspect_and_confirm_sample(work: str) -> None:
    manager().inspectFile(sample_package(work))
    manager().confirmInstall()


def role_of(row: int, role: int) -> object:
    return manager().data(manager().index(row, 0, QModelIndex()), role)


def test_inspect_file_shows_preview(work: str) -> None:
    pending = QSignalSpy(manager().pendingInstallChanged)
    manager().inspectFile(sample_package(work))
    preview = manager().pendingInstall
    assert pending.count() == 1
    assert preview["valid"] and preview["fromFile"]
    assert preview["name"] == "Sample Extension"
    assert preview["installedVersion"] == ""
    assert len(preview["permissions"]) == PERMISSION_COUNT
    assert preview["permissions"][0]["text"] == PREVIEW_PERMISSION
    assert not manager().isInstalled("sample")


def test_confirm_install_installs_the_extension(work: str) -> None:
    inspect_and_confirm_sample(work)
    assert manager().pendingInstall == {}
    assert manager().isInstalled("sample")
    assert manager().source("sample") == "file"
    assert manager().count == 1
    assert (Path(manager().extensions_directory()) / "sample" / "manifest.json").is_file()


def test_confirm_install_fills_the_row(work: str) -> None:
    inspect_and_confirm_sample(work)
    assert role_of(0, Role.NameRole) == "Sample Extension"
    assert role_of(0, Role.EnabledRole) is True
    assert role_of(0, Role.PrivateAllowedRole) is False
    assert role_of(0, Role.HasSettingsRole) is True
    assert role_of(0, Role.HasActionRole) is True


def test_reload_finds_the_install(work: str) -> None:
    inspect_and_confirm_sample(work)
    manager().reload()
    assert manager().count == 1


def test_inspect_again_offers_replacing(work: str) -> None:
    inspect_and_confirm_sample(work)
    manager().inspectFile(sample_package(work))
    assert manager().pendingInstall["installedVersion"] == "1.0.0"
    manager().cancelInstall()
    assert manager().pendingInstall == {}


def test_not_a_zip_shows_error(work: str) -> None:
    not_zip = f"{work}/not-a-zip.kondorext"
    assert write_file(not_zip, b"this is not a zip")
    manager().inspectFile(not_zip)
    preview = manager().pendingInstall
    assert not preview["valid"]
    assert preview["error"]
    assert preview["fileName"] == "not-a-zip.kondorext"


def write_zip_without_manifest(path: str) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.js", "x")


def test_zip_without_manifest_shows_error(work: str) -> None:
    no_manifest = f"{work}/no-manifest.kondorext"
    write_zip_without_manifest(no_manifest)
    manager().inspectFile(no_manifest)
    assert manager().pendingInstall["error"] == "manifest.json: file not found"
    assert manager().count == 0
    directory = Path(manager().extensions_directory())
    assert not directory.exists() or list(directory.iterdir()) == []
