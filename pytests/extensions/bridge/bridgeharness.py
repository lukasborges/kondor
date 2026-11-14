import json
from dataclasses import dataclass
from typing import Any

from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from kondor.extensions.bridge.extensioncall import ExtensionCall
from kondor.extensions.extensionmanager import ExtensionManager

TOKEN_MARKER = '"token":"'


@dataclass
class BridgeClient:
    bridge: ExtensionBridge
    extension_id: str
    token: str

    def call(self, method: str, args: list[Any] | None = None) -> dict[str, Any]:
        reply = self.bridge.request(
            ExtensionCall(self.extension_id, self.token, method, args or [])
        )
        return dict(json.loads(reply))

    def is_ok(self, method: str, args: list[Any] | None = None) -> bool:
        return self.call(method, args).get("ok") is True


def token_of(extension_id: str) -> str:
    source = ExtensionManager.instance().script_source(extension_id, 0, True)
    start = source.find(TOKEN_MARKER)
    if start < 0:
        return ""
    begin = start + len(TOKEN_MARKER)
    return source[begin : source.index('"', begin)]


def sample_token() -> str:
    return token_of("sample")


def error_of(reply: dict[str, Any]) -> str:
    return str(reply.get("error", ""))


class BridgeFixture:
    def __init__(self) -> None:
        self.tab = Tab(None)
        self.bridge = ExtensionBridge()
        self.bridge.tab = self.tab

    def client(self) -> BridgeClient:
        return BridgeClient(self.bridge, "sample", sample_token())
