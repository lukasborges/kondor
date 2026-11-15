import pytest
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from kondor.extensions.userscripts.userscriptmetadata import parse_user_script_metadata
from kondor.extensions.userscripts.userscriptpackage import (
    UserScriptSource,
    user_script_id,
    write_user_script_package,
)
from tests.extensions.bridge.extensionpageharness import (
    PageHost,
    attribute,
    evaluate,
    wait_for_attribute,
)

pytestmark = pytest.mark.no_qt_log

SETTLE_MS = 500
SCRIPT = (
    "// ==UserScript==\n// @name Pages\n// @namespace test\n// @version 1\n"
    "// @match *://127.0.0.1/*\n// @include https://*.example.org/*\n"
    "// @grant GM.addStyle\n// @grant GM.setValue\n"
    "// ==/UserScript==\n"
    "GM.addStyle('body { outline: 5px solid red }');\n"
    "document.documentElement.setAttribute('data-us', 'ran');\n"
    "GM.setValue('n', 7).then(() => GM.getValue('n', 0))\n"
    "  .then((n) => document.documentElement.setAttribute('data-n', String(n)));\n"
)


@pytest.fixture(autouse=True)
def script_installed(work: str, registered_profiles: QQuickWebEngineProfile) -> None:
    metadata, _error = parse_user_script_metadata(SCRIPT)
    path, error = write_user_script_package(UserScriptSource(metadata, SCRIPT.encode()))
    assert path, error
    file = PackageFile(path, "userscript", "", True)
    result = ExtensionManager.instance().install_package(file, user_script_id(metadata))
    assert result.is_installed, result.error


def test_runs_styles_and_stores_values(page_host: PageHost) -> None:
    page = page_host.open_normal()
    wait_for_attribute(page, "data-us", "ran")
    wait_for_attribute(page, "data-n", "7")
    assert evaluate(page, "getComputedStyle(document.body).outlineStyle") == "solid"


def test_does_not_run_in_private_profile(page_host: PageHost) -> None:
    page = page_host.open_private()
    page_host.qtbot.wait(SETTLE_MS)
    assert attribute(page, "data-us") == ""


def test_runs_where_match_or_include_agrees(page_host: PageHost) -> None:
    page = page_host.open_normal()
    wait_for_attribute(page, "data-us", "ran")
