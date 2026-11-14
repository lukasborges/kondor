import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtTest import QSignalSpy

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.install.permissiondescription import permission_lines
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.userscripts.userscriptmetadata import (
    UserScriptMetadata,
    parse_user_script_metadata,
)
from kondor.extensions.userscripts.userscriptpackage import user_script_id
from pytests.extensions.extensionsharness import remove_every_extension

FIXTURES = Path(__file__).resolve().parent.parent.parent / "data" / "userscripts"
WIDE = "wide.user.js"
UNSUPPORTED = ["GM_xmlhttpRequest", "@resource"]
PERMISSION_COUNT = 2
ALL_SITES = "Read and change all websites"


@pytest.fixture
def work(qapp: object, staged_resources: None, tmp_path: Path) -> Iterator[Path]:
    yield tmp_path
    remove_every_extension()


def copy_fixture(work: Path, name: str) -> str:
    for file in (name, "lib.js"):
        shutil.copy(FIXTURES / file, work / file)
    return str(work / name)


def id_of_fixture(path: str) -> str:
    metadata, _error = parse_user_script_metadata(Path(path).read_text())
    return user_script_id(metadata) if metadata else ""


def pending() -> dict[str, Any]:
    return dict(ExtensionManager.instance().pendingInstall)


def wait_for_valid_preview(qtbot: Any) -> None:
    qtbot.waitUntil(lambda: pending().get("valid") is True, timeout=5000)


def test_id_is_stable_for_name_and_namespace(work: Path) -> None:
    identifier = id_of_fixture(copy_fixture(work, WIDE))
    assert ExtensionPackage.is_valid_id(identifier)
    assert identifier.startswith("user-")
    other = UserScriptMetadata(name="Wide Test", namespace_name="test")
    assert user_script_id(other) == identifier
    other.namespace_name = "elsewhere"
    assert user_script_id(other) != identifier


def test_manifest_loads_back_with_include_and_user_script(work: Path, qtbot: Any) -> None:
    manager = ExtensionManager.instance()
    path = copy_fixture(work, WIDE)
    manager.inspectUserScript(QUrl.fromLocalFile(path))
    wait_for_valid_preview(qtbot)
    manager.confirmInstall()
    directory = f"{ExtensionManager.extensions_directory()}/{id_of_fixture(path)}"
    package, error = ExtensionPackage.load(directory)
    assert not error
    assert package.version() == "1.0.0"
    assert package.all_includes() == ["https://*.example.org/*"]
    assert package.user_script()["version"] == "1.0"
    assert package.has_permission("notifications")
    assert not package.content_scripts()[0].all_frames
    assert package.read_file("require-1.js")


@pytest.mark.parametrize(
    ("glob", "expected"),
    [
        ("https://*.example.org/*", ALL_SITES),
        ("file:///*", ALL_SITES),
        ("example.org*", ALL_SITES),
        ("https://example.org/*", "Read and change pages on example.org"),
    ],
    ids=["wildcard host", "empty host", "no scheme", "plain host"],
)
def test_include_globs_describe_site_access(qapp: object, glob: str, expected: str) -> None:
    assert permission_lines([], [], [glob]) == [expected]


def test_installs_file_with_requirement(work: Path, qtbot: Any) -> None:
    manager = ExtensionManager.instance()
    manage = QSignalSpy(manager.manageRequested)
    path = copy_fixture(work, WIDE)
    manager.inspectFile(QUrl.fromLocalFile(path).toString())
    assert manage.count() == 1
    wait_for_valid_preview(qtbot)
    assert pending()["isUserScript"]
    assert pending()["unsupportedFeatures"] == UNSUPPORTED
    assert len(pending()["permissions"]) == PERMISSION_COUNT
    manager.confirmInstall()
    identifier = id_of_fixture(path)
    assert manager.isInstalled(identifier)
    assert manager.source(identifier) == "userscript"
    assert manager.installedVersion(identifier) == "1.0.0"


def test_refuses_invalid_file(work: Path, qtbot: Any) -> None:
    manager = ExtensionManager.instance()
    manager.inspectFile(copy_fixture(work, "no-name.user.js"))
    qtbot.waitUntil(lambda: "valid" in pending(), timeout=5000)
    assert pending()["valid"] is False
    assert pending()["isUserScript"]
    assert pending()["error"]
    manager.cancelInstall()


def test_identical_script_offers_replace(work: Path, qtbot: Any) -> None:
    manager = ExtensionManager.instance()
    url = QUrl.fromLocalFile(copy_fixture(work, WIDE))
    manager.inspectUserScript(url)
    wait_for_valid_preview(qtbot)
    manager.confirmInstall()
    manager.inspectUserScript(url)
    qtbot.waitUntil(lambda: pending().get("installedVersion") == "1.0.0", timeout=5000)
    manager.cancelInstall()
