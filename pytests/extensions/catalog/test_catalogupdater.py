from dataclasses import dataclass

import pytest
from pytestqt.qtbot import QtBot

from kondor.core.settings.settings import Settings
from kondor.extensions.catalog.catalogentry import CatalogEntry
from kondor.extensions.catalog.catalogupdater import UpdateDecision, decide_update
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import install_sample

UNCHANGED = ["*://127.0.0.1/*", "*://localhost/*"]


def sample_entry(version: str, permissions: list[str]) -> CatalogEntry:
    return CatalogEntry(id="sample", version=version, matches=UNCHANGED, permissions=permissions)


def installed_permissions() -> list[str]:
    return ExtensionManager.instance().installed_access("sample").permissions


@dataclass
class UpdateCase:
    source: str | None
    version: str
    extra_permissions: list[str]
    expected: UpdateDecision


UPDATE_CASES = {
    "not-installed": UpdateCase(None, "2.0.0", [], UpdateDecision.NOT_INSTALLED_FROM_CATALOG),
    "file-source": UpdateCase("file", "2.0.0", [], UpdateDecision.NOT_INSTALLED_FROM_CATALOG),
    "same-version": UpdateCase("catalog", "1.0.0", [], UpdateDecision.UP_TO_DATE),
    "silent": UpdateCase("catalog", "2.0.0", [], UpdateDecision.SILENT),
    "needs-review": UpdateCase("catalog", "2.0.0", ["downloads"], UpdateDecision.NEEDS_REVIEW),
}


@pytest.mark.parametrize("case", UPDATE_CASES.values(), ids=UPDATE_CASES.keys())
def test_decides_each_update(work: str, case: UpdateCase) -> None:
    if case.source is not None:
        assert install_sample(work, case.source)
    entry = sample_entry(case.version, installed_permissions() + case.extra_permissions)
    assert decide_update(entry, ExtensionManager.instance()) is case.expected


def test_check_without_catalog_installs_emits_updates_checked_without_refreshing(
    qtbot: QtBot, work: str, auto_update_on: None
) -> None:
    assert install_sample(work, "file")
    catalog = ExtensionCatalog.instance()
    state = catalog.state
    with qtbot.waitSignal(catalog.updatesChecked, timeout=1000):
        catalog.check_for_updates()
    assert catalog.state == state


def test_check_does_nothing_when_auto_update_is_off(qtbot: QtBot, work: str) -> None:
    Settings.instance().setProperty("extensionsAutoUpdate", False)
    catalog = ExtensionCatalog.instance()
    with qtbot.assertNotEmitted(catalog.updatesChecked, wait=200):
        catalog.check_for_updates()
    Settings.instance().setProperty("extensionsAutoUpdate", True)
