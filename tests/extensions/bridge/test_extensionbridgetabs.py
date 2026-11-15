from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.state import extensionstorage
from tests.extensions.bridge.bridgeharness import (
    BridgeClient,
    BridgeFixture,
    error_of,
    sample_token,
)
from tests.extensions.extensionsharness import allow_in_private_windows

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"
ANSWER = 42


@pytest.fixture(autouse=True)
def private_allowed(fixture: BridgeFixture) -> None:
    allow_in_private_windows(SAMPLE)


class PrivateClient:
    def __init__(self) -> None:
        self.profile = QQuickWebEngineProfile()
        self.tab = Tab(self.profile)
        self.bridge = ExtensionBridge()
        self.bridge.tab = self.tab
        self.client = BridgeClient(self.bridge, SAMPLE, sample_token())


def test_private_bridge_reads_but_cannot_write(fixture: BridgeFixture) -> None:
    private = PrivateClient()
    assert private.profile.isOffTheRecord()
    assert private.tab.isPrivate
    assert fixture.client().is_ok("storage.set", ["k", ANSWER])
    read = private.client.call("storage.get", ["k"])
    assert read["ok"] is True
    assert read["value"] == ANSWER
    write = private.client.call("storage.set", ["k", 1])
    assert write["ok"] is False
    assert error_of(write) == "Storage is read-only in private windows"
    assert not private.client.is_ok("storage.remove", ["k"])
    assert extensionstorage.value(SAMPLE, "k") == ANSWER


def test_private_bridge_refused_when_not_allowed(fixture: BridgeFixture) -> None:
    private = PrivateClient()
    assert fixture.client().is_ok("storage.set", ["k", ANSWER])
    assert private.client.is_ok("storage.get", ["k"])
    ExtensionManager.instance().applyConfiguration(SAMPLE, {})
    assert not private.client.is_ok("storage.get", ["k"])
    assert fixture.client().is_ok("storage.get", ["k"])


def test_tab_commands_emit_signals(fixture: BridgeFixture) -> None:
    client = fixture.client()
    closes: list[tuple[Any, ...]] = []
    reloads: list[tuple[Any, ...]] = []
    neighbors: list[int] = []
    fixture.tab.closeRequested.connect(lambda: closes.append(()))
    fixture.tab.reloadRequested.connect(lambda: reloads.append(()))
    fixture.tab.neighborTabRequested.connect(neighbors.append)
    assert client.is_ok("tabs.close")
    assert len(closes) == 1
    assert client.is_ok("tabs.reload")
    assert len(reloads) == 1
    assert client.is_ok("tabs.next")
    assert client.is_ok("tabs.previous")
    assert neighbors == [1, -1]


def test_tab_open_accepts_only_web_addresses(fixture: BridgeFixture) -> None:
    client = fixture.client()
    opens: list[tuple[QUrl, bool]] = []
    fixture.tab.openTabRequested.connect(lambda url, background: opens.append((url, background)))
    assert client.is_ok("tabs.open", ["https://example.com/", True])
    assert opens == [(QUrl("https://example.com/"), True)]
    assert not client.is_ok("tabs.open", ["file:///etc/passwd", False])
    assert not client.is_ok("tabs.open", ["javascript:alert(1)", False])
    assert len(opens) == 1


def test_unknown_method_is_refused(fixture: BridgeFixture) -> None:
    assert not fixture.client().is_ok("no.such.method")


def test_toolbar_item_checked_state_is_per_tab(fixture: BridgeFixture) -> None:
    assert fixture.client().is_ok("action.setChecked", ["toggle", True])
    items = fixture.tab.extensionItems
    assert items.isChecked(SAMPLE, "toggle")
    assert not Tab(None).extensionItems.isChecked(SAMPLE, "toggle")
    triggered: list[tuple[Any, ...]] = []
    items.triggered.connect(lambda *args: triggered.append(args))
    items.trigger(SAMPLE, "toggle", True)
    assert not items.isChecked(SAMPLE, "toggle")
    assert len(triggered) == 1
    assert triggered[0][2] is False
