from collections.abc import Callable
from typing import NamedTuple

from kondor.extensions.bridge import bridgestorage, bridgetabs
from kondor.extensions.bridge.bridgecontext import BridgeContext
from kondor.extensions.bridge.extensioncall import error_reply
from kondor.extensions.extensionmanager import ExtensionManager

__all__ = ["BridgeContext", "handle_bridge_call", "required_permission"]


class BridgeMethod(NamedTuple):
    permission: str
    handler: Callable[[BridgeContext], str]


METHODS: dict[str, BridgeMethod] = {
    "storage.get": BridgeMethod("", bridgestorage.storage_get),
    "storage.keys": BridgeMethod("", bridgestorage.storage_keys),
    "storage.set": BridgeMethod("", bridgestorage.storage_set),
    "storage.remove": BridgeMethod("", bridgestorage.storage_remove),
    "action.setChecked": BridgeMethod("", bridgestorage.set_action_checked),
    "tabs.back": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.forward": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.reload": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.close": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.next": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.previous": BridgeMethod("tabs", bridgetabs.run_tab_command),
    "tabs.open": BridgeMethod("tabs", bridgetabs.open_tab),
    "download": BridgeMethod("downloads", bridgetabs.download),
    "notify": BridgeMethod("notifications", bridgetabs.notify),
}


def required_permission(method: str) -> str:
    if method.startswith("tabs."):
        return "tabs"
    entry = METHODS.get(method)
    return entry.permission if entry is not None else ""


def denied_reply(permission: str) -> str:
    return error_reply(f'Permission denied: this needs the "{permission}" permission')


def lacks_permission(context: BridgeContext, permission: str) -> bool:
    manager = ExtensionManager.instance()
    return bool(permission) and not manager.has_permission(context.call.extension_id, permission)


def handle_bridge_call(context: BridgeContext) -> str:
    permission = required_permission(context.call.method)
    if lacks_permission(context, permission):
        return denied_reply(permission)
    entry = METHODS.get(context.call.method)
    if entry is None:
        return error_reply(f"Unknown method: {context.call.method}")
    return entry.handler(context)
