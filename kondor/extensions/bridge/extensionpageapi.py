from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Slot

from kondor.extensions.bridge.extensioncall import parse_extension_call

if TYPE_CHECKING:
    from kondor.extensions.bridge.extensionbridge import ExtensionBridge


class ExtensionPageApi(QObject):
    def __init__(self, bridge: "ExtensionBridge") -> None:
        super().__init__(bridge)
        self._bridge = bridge

    @Slot(str, result=str)
    def request(self, request_json: str) -> str:
        return self._bridge.request(parse_extension_call(request_json))
