from pathlib import Path

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.state.extensionaccess import ExtensionAccess, is_silent_update
from pytests.extensions.catalog.catalogharness import (
    WAIT_MILLISECONDS,
    CatalogFixture,
    catalog_fixture,
    refresh_catalog,
    wait_for_pending_install,
    write_catalog,
)

MATCHES = ["https://a.com/*", "https://b.com/*"]
PERMISSIONS = ["tabs"]
INSTALLED = ExtensionAccess(MATCHES, PERMISSIONS)


def fixture(root: str, version: str = "1.0.0") -> CatalogFixture:
    return catalog_fixture(root, version, ["tabs"])


def row_role(catalog: ExtensionCatalog, role: int) -> object:
    return catalog.data(catalog.index(0, 0), role)


def test_silent_update_rule() -> None:
    assert is_silent_update(ExtensionAccess(MATCHES, PERMISSIONS), INSTALLED)
    assert is_silent_update(ExtensionAccess(["https://a.com/*"], []), INSTALLED)
    assert is_silent_update(ExtensionAccess([], []), INSTALLED)
    assert not is_silent_update(ExtensionAccess(["https://c.com/*"], PERMISSIONS), INSTALLED)
    assert not is_silent_update(ExtensionAccess(MATCHES, ["tabs", "downloads"]), INSTALLED)
    assert not is_silent_update(ExtensionAccess(["<all_urls>"], PERMISSIONS), INSTALLED)


def test_catalog_lists_entries(qtbot: QtBot, catalog_root: str) -> None:
    catalog = ExtensionCatalog.instance()
    assert refresh_catalog(qtbot, catalog, write_catalog(fixture(catalog_root)))
    assert catalog.rowCount() == 1
    assert row_role(catalog, ExtensionCatalog.Role.IdRole) == "sample"
    assert row_role(catalog, ExtensionCatalog.Role.NameRole) != ""
    assert row_role(catalog, ExtensionCatalog.Role.IconSourceRole) == "weather-clear-night"
    assert not row_role(catalog, ExtensionCatalog.Role.InstalledRole)
    assert Path(ExtensionCatalog.cache_file()).is_file()


def test_catalog_install_asks_for_confirmation(qtbot: QtBot, catalog_root: str) -> None:
    catalog, manager = ExtensionCatalog.instance(), ExtensionManager.instance()
    assert refresh_catalog(qtbot, catalog, write_catalog(fixture(catalog_root)))
    catalog.install("sample")
    wait_for_pending_install(qtbot)
    assert manager.pendingInstall["valid"]
    assert not manager.pendingInstall["fromFile"]
    assert not manager.isInstalled("sample")
    manager.confirmInstall()
    assert manager.isInstalled("sample")
    assert manager.source("sample") == "catalog"
    assert row_role(catalog, ExtensionCatalog.Role.InstalledRole)
    assert catalog.installError == ""


def wait_for_install_error(qtbot: QtBot, catalog: ExtensionCatalog) -> None:
    qtbot.waitUntil(lambda: catalog.installError != "", timeout=WAIT_MILLISECONDS)


def assert_nothing_to_install(catalog: ExtensionCatalog) -> None:
    assert ExtensionManager.instance().pendingInstall == {}
    assert not ExtensionManager.instance().isInstalled("sample")
    assert catalog.installingId == ""


def test_catalog_rejects_bad_checksum(qtbot: QtBot, catalog_root: str) -> None:
    broken = fixture(catalog_root)
    broken.checksum = "0" * 64
    catalog = ExtensionCatalog.instance()
    assert refresh_catalog(qtbot, catalog, write_catalog(broken))
    catalog.install("sample")
    wait_for_install_error(qtbot, catalog)
    assert "checksum" in catalog.installError
    assert_nothing_to_install(catalog)


def test_catalog_rejects_oversized_package(qtbot: QtBot, catalog_root: str) -> None:
    oversized = fixture(catalog_root)
    oversized.size = 10
    catalog = ExtensionCatalog.instance()
    assert refresh_catalog(qtbot, catalog, write_catalog(oversized))
    catalog.install("sample")
    wait_for_install_error(qtbot, catalog)
    assert_nothing_to_install(catalog)


def test_failed_refresh_keeps_the_entries(qtbot: QtBot, catalog_root: str) -> None:
    catalog = ExtensionCatalog.instance()
    assert refresh_catalog(qtbot, catalog, write_catalog(fixture(catalog_root)))
    assert not refresh_catalog(qtbot, catalog, QUrl.fromLocalFile(f"{catalog_root}/missing.json"))
    assert catalog.state == "ready"
    assert catalog.errorString != ""
    assert catalog.rowCount() == 1


def test_failed_first_refresh_is_an_error(qtbot: QtBot, catalog_root: str) -> None:
    Path(ExtensionCatalog.cache_file()).unlink(missing_ok=True)
    fresh = ExtensionCatalog()
    assert not refresh_catalog(qtbot, fresh, QUrl.fromLocalFile(f"{catalog_root}/missing.json"))
    assert fresh.state == "error"
    fresh.deleteLater()


def test_cached_catalog_is_shown_at_start(qtbot: QtBot, catalog_root: str) -> None:
    assert refresh_catalog(qtbot, ExtensionCatalog.instance(), write_catalog(fixture(catalog_root)))
    cached = ExtensionCatalog()
    assert (cached.state, cached.rowCount()) == ("ready", 1)
    cached.deleteLater()
