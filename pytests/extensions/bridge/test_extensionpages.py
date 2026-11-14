import json
from collections.abc import Iterator

import pytest
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.state import extensionstorage
from pytests.extensions.bridge.extensionpageharness import (
    PageHost,
    attribute,
    evaluate,
    load_url,
    run_in_application_world,
    wait_for_attribute,
    wait_loaded,
)
from pytests.extensions.extensionsharness import (
    allow_in_private_windows,
    apply_settings,
    install_sample,
)

pytestmark = pytest.mark.no_qt_log

SETTLE_MS = 500
SHORT_SETTLE_MS = 300
ATTRIBUTE = "data-kondor-sample"
ATTRIBUTE_TIMEOUT = 10000


@pytest.fixture(autouse=True)
def sample_installed(work: str, registered_profiles: QQuickWebEngineProfile) -> Iterator[None]:
    assert install_sample(work)
    yield


def test_runs_in_normal_pages_with_settings_and_storage(page_host: PageHost) -> None:
    normal = page_host.open_normal()
    wait_for_attribute(normal, ATTRIBUTE, "hello")
    assert attribute(normal, "data-kondor-private") == "false"
    wait_for_attribute(normal, "data-kondor-storage", "ok")
    assert extensionstorage.value("sample", "lastGreeting") == "hello"


def test_setting_change_reaches_the_open_page(page_host: PageHost) -> None:
    normal = page_host.open_normal()
    wait_for_attribute(normal, ATTRIBUTE, "hello")
    apply_settings("sample", {"greeting": "hola"})
    values = json.dumps(ExtensionManager.instance().settingValues("sample"), separators=(",", ":"))
    run_in_application_world(normal, f"window.__kondorExtensions['sample']({values});")
    wait_for_attribute(normal, ATTRIBUTE, "hola")


def test_toolbar_action_reaches_the_extension(page_host: PageHost) -> None:
    normal = page_host.open_normal()
    wait_for_attribute(normal, ATTRIBUTE, "hello")
    run_in_application_world(normal, "window.__kondorExtensionActions['sample']('toggle', true);")
    wait_for_attribute(normal, "data-kondor-action", "toggle:true")


def test_excluded_path_does_not_run_it(page_host: PageHost) -> None:
    excluded = page_host.open_normal("/excluded/page")
    page_host.qtbot.wait(SETTLE_MS)
    assert attribute(excluded, ATTRIBUTE) == ""


def test_private_pages_need_permission_and_get_read_only_storage(page_host: PageHost) -> None:
    private = page_host.open_private()
    page_host.qtbot.wait(SETTLE_MS)
    assert attribute(private, ATTRIBUTE) == ""
    allow_in_private_windows("sample")
    page_host.qtbot.wait(SHORT_SETTLE_MS)
    load_url(private.view, page_host.server.url("/again"))
    wait_loaded(private)
    wait_for_attribute(private, "data-kondor-private", "true")
    page_host.qtbot.waitUntil(
        lambda: "read-only" in attribute(private, "data-kondor-storage"),
        timeout=ATTRIBUTE_TIMEOUT,
    )


def test_disabled_site_does_not_run_it(page_host: PageHost) -> None:
    normal = page_host.open_normal()
    wait_for_attribute(normal, ATTRIBUTE, "hello")
    ExtensionManager.instance().setSiteEnabled("sample", page_host.server.url(), False)
    page_host.qtbot.wait(SHORT_SETTLE_MS)
    load_url(normal.view, page_host.server.url("/after-toggle"))
    wait_loaded(normal)
    page_host.qtbot.wait(SETTLE_MS)
    assert evaluate(normal, "location.pathname") == "/after-toggle"
    assert attribute(normal, ATTRIBUTE) == ""
