import json
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from shiboken6 import delete

from kondor.browser.tabs.tab import Tab
from kondor.core.notifier import Notifier
from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from kondor.extensions.bridge.extensioncall import error_reply, ok_reply
from kondor.extensions.bridge.extensionpageapi import ExtensionPageApi
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from tests.extensions.bridge.bridgeharness import BridgeFixture, error_of, sample_token
from tests.extensions.extensionsharness import allow_in_private_windows, pack_variant

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"
FORTY_TWO = 42


def test_replies_are_compact_json_with_sorted_keys() -> None:
    assert ok_reply() == '{"ok":true,"value":null}'
    assert ok_reply(42.0) == '{"ok":true,"value":42}'
    assert error_reply("x") == '{"error":"x","ok":false}'
    assert error_reply("é") == '{"error":"é","ok":false}'


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("storage.get", "The key must be a string"),
        ("tabs.open", "Only http and https addresses can be opened"),
        ("action.setChecked", ""),
    ],
)
def test_missing_arguments_are_refused_not_raised(
    fixture: BridgeFixture, method: str, expected: str
) -> None:
    allow_in_private_windows(SAMPLE)
    reply = fixture.client().call(method)
    assert error_of(reply) == expected
    assert reply["ok"] is (expected == "")


def test_tab_commands_reach_back_and_forward(fixture: BridgeFixture) -> None:
    events: list[str] = []
    fixture.tab.backRequested.connect(lambda: events.append("back"))
    fixture.tab.forwardRequested.connect(lambda: events.append("forward"))
    assert fixture.client().is_ok("tabs.back")
    assert fixture.client().is_ok("tabs.forward")
    assert events == ["back", "forward"]


def test_download_reaches_the_tab(fixture: BridgeFixture, work: str) -> None:
    zip_path = pack_variant(
        work, "downloads", lambda manifest: manifest.update(permissions=["downloads"])
    )
    installed = ExtensionManager.instance().install_package(PackageFile(zip_path, "file"), SAMPLE)
    assert installed.is_installed, installed.error
    downloads: list[tuple[QUrl, str]] = []
    fixture.tab.downloadUrlRequested.connect(lambda url, name: downloads.append((url, name)))
    client = fixture.client()
    assert client.is_ok("download", ["https://example.com/f.zip", "f.zip"])
    assert downloads == [(QUrl("https://example.com/f.zip"), "f.zip")]
    refused = client.call("download", ["file:///etc/passwd", ""])
    assert error_of(refused) == "Only http and https addresses can be downloaded"


def test_notify_prefixes_the_extension_name(
    fixture: BridgeFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        Notifier.instance(), "notify", lambda title, body, icon: sent.append((title, body, icon))
    )
    assert fixture.client().is_ok("notify", ["t", "b"])
    assert sent == [("Sample Extension: t", "b", "preferences-plugin")]


def test_destroyed_tab_gives_no_tab(fixture: BridgeFixture, qtbot: Any) -> None:
    delete(fixture.tab)
    qtbot.wait(0)
    assert error_of(fixture.client().call("storage.keys")) == "No tab"


def test_replaced_tab_destroyed_keeps_current_tab(fixture: BridgeFixture, qtbot: Any) -> None:
    current = Tab(None)
    fixture.bridge.tab = current
    delete(fixture.tab)
    qtbot.wait(0)
    assert fixture.bridge.tab is current


def test_page_api_keeps_the_channel_name(fixture: BridgeFixture) -> None:
    api = fixture.bridge.pageApi()
    meta = api.metaObject()
    index = meta.indexOfMethod("request(QString)")
    assert index >= 0
    assert meta.method(index).typeName() == "QString"
    assert fixture.bridge.pageApi() is api
    assert isinstance(api, ExtensionPageApi)
    assert isinstance(fixture.bridge, ExtensionBridge)


def test_page_api_forwards_to_the_bridge(fixture: BridgeFixture) -> None:
    allow_in_private_windows(SAMPLE)
    request = json.dumps({"id": SAMPLE, "token": sample_token(), "method": "storage.keys"})
    assert fixture.bridge.pageApi().request(request) == '{"ok":true,"value":[]}'
