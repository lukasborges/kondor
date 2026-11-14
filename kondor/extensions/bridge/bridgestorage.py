from kondor.extensions.bridge.bridgecontext import BridgeContext
from kondor.extensions.bridge.extensioncall import (
    argument,
    bool_argument,
    error_reply,
    ok_reply,
    string_argument,
)
from kondor.extensions.state import extensionstorage


def key_refusal(context: BridgeContext) -> str:
    if isinstance(argument(context.call, 0), str):
        return ""
    return error_reply("The key must be a string")


def write_refusal(context: BridgeContext) -> str:
    if context.tab.isPrivate:
        return error_reply("Storage is read-only in private windows")
    return key_refusal(context)


def storage_get(context: BridgeContext) -> str:
    refusal = key_refusal(context)
    if refusal:
        return refusal
    return ok_reply(
        extensionstorage.value(context.call.extension_id, string_argument(context.call, 0))
    )


def storage_keys(context: BridgeContext) -> str:
    return ok_reply(extensionstorage.keys(context.call.extension_id))


def storage_set(context: BridgeContext) -> str:
    refusal = write_refusal(context)
    if refusal:
        return refusal
    call = context.call
    write = extensionstorage.set_value(
        call.extension_id, string_argument(call, 0), argument(call, 1)
    )
    return ok_reply() if write.is_written else error_reply(write.error)


def storage_remove(context: BridgeContext) -> str:
    refusal = write_refusal(context)
    if refusal:
        return refusal
    extensionstorage.remove_value(context.call.extension_id, string_argument(context.call, 0))
    return ok_reply()


def set_action_checked(context: BridgeContext) -> str:
    call = context.call
    context.tab.extensionItems.setChecked(
        call.extension_id, string_argument(call, 0), bool_argument(call, 1)
    )
    return ok_reply()
