import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from tests.extensions.extensionsharness import (
    make_variant,
    sha256_of,
    write_file,
    zip_directory,
)

WAIT_MILLISECONDS = 10000
SAMPLE_MATCHES = ["*://127.0.0.1/*", "*://localhost/*"]


@dataclass
class CatalogFixture:
    root: str
    version: str
    permissions: list[str]
    checksum: str = ""
    size: int = -1
    catalog_permissions: list[str] | None = field(default=None)


def catalog_fixture(root: str, version: str, permissions: list[str]) -> CatalogFixture:
    return CatalogFixture(root, version, permissions)


def pack_catalog_package(fixture: CatalogFixture) -> str:
    def edit(manifest: dict[str, Any]) -> None:
        manifest["version"] = fixture.version
        manifest["permissions"] = fixture.permissions

    directory = make_variant(fixture.root, f"pkg-{fixture.version}", edit)
    zip_path = f"{fixture.root}/packages/sample-{fixture.version}.kondorext"
    Path(zip_path).parent.mkdir(parents=True, exist_ok=True)
    zip_directory(directory, zip_path)
    return zip_path


def advertised_permissions(fixture: CatalogFixture) -> list[str]:
    return (
        fixture.permissions if fixture.catalog_permissions is None else fixture.catalog_permissions
    )


def catalog_entry(fixture: CatalogFixture, zip_path: str) -> dict[str, Any]:
    return {
        "id": "sample",
        "name": "Sample Extension",
        "name[pt_BR]": "Extensão de Exemplo",
        "description": "Marks pages.",
        "version": fixture.version,
        "author": "Kondor contributors",
        "icon": "weather-clear-night",
        "permissions": advertised_permissions(fixture),
        "matches": SAMPLE_MATCHES,
        "package": f"packages/sample-{fixture.version}.kondorext",
        "sha256": fixture.checksum or sha256_of(zip_path),
        "size": fixture.size if fixture.size >= 0 else Path(zip_path).stat().st_size,
    }


def write_catalog(fixture: CatalogFixture) -> QUrl:
    entry = catalog_entry(fixture, pack_catalog_package(fixture))
    catalog = {"version": 1, "generated": "2026-11-10T21:00:00Z", "extensions": [entry]}
    path = f"{fixture.root}/catalog.json"
    write_file(path, json.dumps(catalog).encode())
    return QUrl.fromLocalFile(path)


def refresh_catalog(qtbot: QtBot, catalog: ExtensionCatalog, url: QUrl) -> bool:
    catalog.set_catalog_url(url)
    with qtbot.waitSignal(catalog.updatesChecked, timeout=WAIT_MILLISECONDS):
        catalog.refresh()
    return catalog.state == "ready" and catalog.errorString == ""


def wait_for_pending_install(qtbot: QtBot) -> None:
    manager = ExtensionManager.instance()
    qtbot.waitUntil(lambda: bool(manager.pendingInstall), timeout=WAIT_MILLISECONDS)


def install_from_catalog(qtbot: QtBot, fixture: CatalogFixture) -> None:
    assert refresh_catalog(qtbot, ExtensionCatalog.instance(), write_catalog(fixture))
    ExtensionCatalog.instance().install("sample")
    wait_for_pending_install(qtbot)
    ExtensionManager.instance().confirmInstall()
    assert installed_sample_version() == fixture.version


def is_update_waiting_for_review() -> bool:
    manager = ExtensionManager.instance()
    return bool(manager.data(manager.index(0, 0), ExtensionManager.Role.UpdateNeedsReviewRole))


def installed_sample_version() -> str:
    return ExtensionManager.instance().installedVersion("sample")
