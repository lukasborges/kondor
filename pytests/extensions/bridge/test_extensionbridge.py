import pytest

from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from kondor.extensions.state import extensionstorage
from pytests.extensions.bridge.bridgeharness import (
    BridgeClient,
    BridgeFixture,
    error_of,
    sample_token,
)
from pytests.extensions.extensionsharness import allow_in_private_windows, pack_variant

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"


def test_storage_quota(fixture: BridgeFixture) -> None:
    assert extensionstorage.set_value(SAMPLE, "a", "x" * 600 * 1024).is_written
    error = extensionstorage.set_value(SAMPLE, "b", "y" * 600 * 1024).error
    assert "full" in error
    assert "b" not in extensionstorage.keys(SAMPLE)
    assert extensionstorage.set_value(SAMPLE, "a", "z" * 900 * 1024).is_written
    extensionstorage.remove_value(SAMPLE, "a")
    stored = {"n": 1, "list": [1, 2]}
    assert extensionstorage.set_value(SAMPLE, "obj", stored).is_written
    assert extensionstorage.value(SAMPLE, "obj") == stored
    assert extensionstorage.value(SAMPLE, "missing") is None


def test_storage_is_per_extension(fixture: BridgeFixture) -> None:
    assert extensionstorage.set_value(SAMPLE, "k", 1).is_written
    assert extensionstorage.value("other", "k") is None
    assert extensionstorage.keys(SAMPLE) == ["k"]
    assert extensionstorage.keys("other") == []


def test_bridge_rejects_wrong_token(fixture: BridgeFixture) -> None:
    allow_in_private_windows(SAMPLE)
    good = sample_token()
    assert good
    assert fixture.client().is_ok("storage.keys")
    wrong = BridgeClient(fixture.bridge, SAMPLE, "wrong")
    assert error_of(wrong.call("storage.keys")) == "Invalid extension token"
    assert not BridgeClient(fixture.bridge, SAMPLE, "").is_ok("storage.keys")
    assert not BridgeClient(fixture.bridge, "other", good).is_ok("storage.keys")
    assert not BridgeClient(ExtensionBridge(), SAMPLE, good).is_ok("storage.keys")


def test_bridge_refuses_download_without_permission(fixture: BridgeFixture) -> None:
    allow_in_private_windows(SAMPLE)
    reply = fixture.client().call("download", ["https://example.com/f.zip", ""])
    assert reply["ok"] is False
    assert '"downloads"' in error_of(reply)


def install_sample_without_tabs_permission(work: str) -> None:
    zip_path = pack_variant(work, "notabs", lambda manifest: manifest.update(permissions=[]))
    installed = ExtensionManager.instance().install_package(PackageFile(zip_path, "file"), SAMPLE)
    assert installed.is_installed, installed.error
    allow_in_private_windows(SAMPLE)


def test_bridge_refuses_tabs_without_permission(fixture: BridgeFixture, work: str) -> None:
    good = sample_token()
    allow_in_private_windows(SAMPLE)
    install_sample_without_tabs_permission(work)
    without_tabs = fixture.client()
    assert without_tabs.token != good
    closes: list[bool] = []
    fixture.tab.closeRequested.connect(lambda: closes.append(True))
    reply = without_tabs.call("tabs.close")
    assert reply["ok"] is False
    assert '"tabs"' in error_of(reply)
    assert not closes
    assert not without_tabs.is_ok("notify", ["t", "b"])


def test_bridge_off_extension(fixture: BridgeFixture) -> None:
    good = fixture.client()
    allow_in_private_windows(SAMPLE)
    ExtensionManager.instance().setEnabled(SAMPLE, False)
    assert not good.is_ok("storage.keys")
    assert error_of(good.call("storage.keys")) == "The extension is turned off"
