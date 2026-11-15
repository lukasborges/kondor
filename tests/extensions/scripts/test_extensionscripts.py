from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineScript

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from tests.extensions.extensionsharness import (
    allow_in_private_windows,
    install_sample,
    pack_variant,
    remove_every_extension,
)

InjectionPoint = QWebEngineScript.InjectionPoint
APPLICATION_WORLD = QWebEngineScript.ScriptWorldId.ApplicationWorld.value
EXAMPLE_URL = QUrl("https://example.com/page?q=1")


@pytest.fixture
def work(qapp: object, staged_resources: None, tmp_path: Path) -> Iterator[str]:
    yield str(tmp_path)
    remove_every_extension()


def sample_script(is_private: bool) -> str:
    return ExtensionManager.instance().script_source("sample", 0, is_private)


def run_at_edit(run_at: str) -> Any:
    def edit(manifest: dict[str, Any]) -> None:
        script = manifest["contentScripts"][0]
        script["runAt"] = run_at
        script["allFrames"] = True

    return edit


def test_script_metadata(work: str) -> None:
    assert install_sample(work)
    source = sample_script(False)
    assert source.startswith("// ==UserScript==\n")
    assert "// @match *://127.0.0.1/*\n" in source
    assert "// @match *://localhost/*\n" in source
    assert "// @exclude *://127.0.0.1:*/excluded/*\n" in source
    assert "// @run-at document-end\n// ==/UserScript==\n" in source
    assert "border-top: 4px solid #3daee9" in source
    assert "data-kondor-sample" in source
    assert "__kondorCreateRuntime" in source
    assert '"token":""' not in source


def test_scripts_for_normal_profile(work: str) -> None:
    assert install_sample(work)
    scripts = ExtensionManager.instance().scripts_for(False)
    assert len(scripts) == 1
    assert scripts[0].name() == "kondor-ext:sample:0"
    assert scripts[0].worldId() == APPLICATION_WORLD
    assert not scripts[0].runsOnSubFrames()


@pytest.mark.parametrize(
    ("run_at", "point"),
    [
        ("document-start", InjectionPoint.DocumentCreation),
        ("document-end", InjectionPoint.DocumentReady),
        ("document-idle", InjectionPoint.Deferred),
    ],
    ids=["start", "end", "idle"],
)
def test_run_at_mapping(work: str, run_at: str, point: InjectionPoint) -> None:
    zip_path = pack_variant(work, "runat", run_at_edit(run_at))
    manager = ExtensionManager.instance()
    installed = manager.install_package(PackageFile(zip_path, "file"), "sample")
    assert installed.is_installed, installed.error
    scripts = manager.scripts_for(False)
    assert len(scripts) == 1
    assert scripts[0].injectionPoint() == point
    assert scripts[0].runsOnSubFrames()
    assert f"// @run-at {run_at}\n" in scripts[0].sourceCode()


def test_private_profile_scripts(work: str) -> None:
    assert install_sample(work)
    manager = ExtensionManager.instance()
    assert len(manager.scripts_for(True)) == 0
    assert len(manager.scripts_for(False)) == 1
    allow_in_private_windows("sample")
    assert len(manager.scripts_for(True)) == 1
    assert '"isPrivate":true' in sample_script(True)
    manager.setEnabled("sample", False)
    assert len(manager.scripts_for(False)) == 0
    assert len(manager.scripts_for(True)) == 0


def test_disabled_site_is_in_script(work: str) -> None:
    assert install_sample(work)
    manager = ExtensionManager.instance()
    assert manager.siteEnabled("sample", EXAMPLE_URL)
    manager.setSiteEnabled("sample", EXAMPLE_URL, False)
    assert not manager.siteEnabled("sample", EXAMPLE_URL)
    assert manager.siteEnabled("sample", QUrl("https://other.example/"))
    assert '"disabledSites":["https://example.com"]' in sample_script(False)
    assert manager.configurationFor("sample")["disabledSites"] == ["https://example.com"]
    manager.setSiteEnabled("sample", EXAMPLE_URL, True)
    assert manager.siteEnabled("sample", EXAMPLE_URL)
    assert manager.originOf(QUrl("file:///tmp/a.html")) == ""
    assert manager.originOf(QUrl("https://Example.com:8443/x")) == "https://example.com:8443"
