from collections.abc import Iterator

import pytest
from pytestqt.qtbot import QtBot

from kondor.core.settings.settings import Settings
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.catalog.catalogharness import (
    WAIT_MILLISECONDS,
    CatalogFixture,
    catalog_fixture,
    install_from_catalog,
    installed_sample_version,
    is_update_waiting_for_review,
    refresh_catalog,
    wait_for_pending_install,
    write_catalog,
)
from pytests.extensions.extensionsharness import install_sample

TABS = ["tabs"]
WITH_DOWNLOADS = ["tabs", "downloads"]
SETTLE_MILLISECONDS = 300


@pytest.fixture(autouse=True)
def automatic_updates(auto_update_on: None) -> Iterator[None]:
    yield


def publish(qtbot: QtBot, fixture: CatalogFixture) -> None:
    assert refresh_catalog(qtbot, ExtensionCatalog.instance(), write_catalog(fixture))


def wait_for_version(qtbot: QtBot, version: str) -> None:
    qtbot.waitUntil(lambda: installed_sample_version() == version, timeout=WAIT_MILLISECONDS)


def test_newer_version_without_new_permissions_installs_itself(
    qtbot: QtBot, catalog_root: str
) -> None:
    manager = ExtensionManager.instance()
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.0.0", TABS))
    publish(qtbot, catalog_fixture(catalog_root, "1.1.0", TABS))
    wait_for_version(qtbot, "1.1.0")
    assert manager.pendingInstall == {}
    row = manager.index(0, 0)
    assert not manager.data(row, ExtensionManager.Role.UpdateAvailableRole)


def test_new_permission_only_marks_update_for_review(qtbot: QtBot, catalog_root: str) -> None:
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.1.0", TABS))
    publish(qtbot, catalog_fixture(catalog_root, "1.2.0", WITH_DOWNLOADS))
    qtbot.waitUntil(is_update_waiting_for_review, timeout=WAIT_MILLISECONDS)
    assert installed_sample_version() == "1.1.0"
    catalog = ExtensionCatalog.instance()
    assert catalog.data(catalog.index(0, 0), ExtensionCatalog.Role.UpdateAvailableRole)


def test_catalog_claiming_old_permissions_is_not_silent(qtbot: QtBot, catalog_root: str) -> None:
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.1.0", TABS))
    claiming = catalog_fixture(catalog_root, "1.1.5", WITH_DOWNLOADS)
    claiming.catalog_permissions = TABS
    assert refresh_catalog(qtbot, ExtensionCatalog.instance(), write_catalog(claiming))
    qtbot.waitUntil(is_update_waiting_for_review, timeout=WAIT_MILLISECONDS)
    assert installed_sample_version() == "1.1.0"
    access = ExtensionManager.instance().installed_access("sample")
    assert "downloads" not in access.permissions


def test_update_asks_first_with_replacement_text(qtbot: QtBot, catalog_root: str) -> None:
    manager = ExtensionManager.instance()
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.1.0", TABS))
    publish(qtbot, catalog_fixture(catalog_root, "1.2.0", WITH_DOWNLOADS))
    qtbot.wait(SETTLE_MILLISECONDS)
    assert installed_sample_version() == "1.1.0"
    ExtensionCatalog.instance().install("sample")
    wait_for_pending_install(qtbot)
    assert manager.pendingInstall["installedVersion"] == "1.1.0"
    assert manager.pendingInstall["version"] == "1.2.0"
    manager.confirmInstall()
    assert installed_sample_version() == "1.2.0"


def test_nothing_updates_when_automatic_updates_are_off(qtbot: QtBot, catalog_root: str) -> None:
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.2.0", WITH_DOWNLOADS))
    Settings.instance().setProperty("extensionsAutoUpdate", False)
    publish(qtbot, catalog_fixture(catalog_root, "1.3.0", WITH_DOWNLOADS))
    qtbot.wait(SETTLE_MILLISECONDS)
    assert installed_sample_version() == "1.2.0"


def test_file_installs_are_never_updated_automatically(
    qtbot: QtBot, catalog_root: str, work: str
) -> None:
    install_from_catalog(qtbot, catalog_fixture(catalog_root, "1.2.0", WITH_DOWNLOADS))
    assert install_sample(work, "file")
    assert installed_sample_version() == "1.0.0"
    publish(qtbot, catalog_fixture(catalog_root, "1.3.0", WITH_DOWNLOADS))
    qtbot.wait(SETTLE_MILLISECONDS)
    assert installed_sample_version() == "1.0.0"
