import pytest

from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from kondor.extensions.bridge.extensioncall import ExtensionCall, parse_extension_call
from pytests.extensions.bridge.bridgeharness import BridgeClient, error_of, sample_token
from pytests.extensions.extensionsharness import allow_in_private_windows, install_sample

pytestmark = pytest.mark.no_qt_log


def test_parses_the_request_object() -> None:
    call = parse_extension_call(
        '{"id":"sample","token":"t","method":"tabs.back","arguments":[1,"a"]}'
    )
    assert (call.extension_id, call.token, call.method) == ("sample", "t", "tabs.back")
    assert call.arguments == [1, "a"]


@pytest.mark.parametrize(
    "request_json",
    ["not json", "[]", '{"id":3,"arguments":"x"}'],
    ids=["not-json", "array", "wrong-types"],
)
def test_malformed_request_gives_empty_fields(request_json: str) -> None:
    call = parse_extension_call(request_json)
    assert call == ExtensionCall("", "", "", [])


def test_bridge_rejects_unknown_tabs_method_after_permission_check(work: str) -> None:
    assert install_sample(work)
    allow_in_private_windows("sample")
    tab = Tab(None)
    bridge = ExtensionBridge()
    bridge.tab = tab
    client = BridgeClient(bridge, "sample", sample_token())
    assert error_of(client.call("tabs.nope")) == "Unknown method: tabs.nope"
