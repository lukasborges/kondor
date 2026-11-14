from typing import Any

from kondor.extensions.manifest.jsonvalue import UNDEFINED, string_at, to_array, to_object

SETTING_TYPES = ("bool", "number", "string", "text", "choice", "color", "keys")


def manifest_error(message: str) -> str:
    return "manifest.json: " + message


def key_error(setting: dict[str, Any], where: str, keys: set[str]) -> str:
    key = string_at(setting, "key")
    if not key or key in keys:
        return manifest_error(f"{where}.key: required and unique")
    keys.add(key)
    return ""


def type_error(setting: dict[str, Any], where: str) -> str:
    if string_at(setting, "type") in SETTING_TYPES:
        return ""
    return manifest_error(f"{where}.type: unknown setting type")


def label_error(setting: dict[str, Any], where: str) -> str:
    if string_at(setting, "label"):
        return ""
    return manifest_error(f"{where}.label: required")


def is_choice_without_choices(setting: dict[str, Any]) -> bool:
    return string_at(setting, "type") == "choice" and not to_array(setting.get("choices"))


def choices_error(setting: dict[str, Any], where: str) -> str:
    if not is_choice_without_choices(setting):
        return ""
    return manifest_error(f"{where}.choices: required for a choice")


def setting_error(setting: dict[str, Any], index: int, keys: set[str]) -> str:
    where = f"settings[{index}]"
    error = key_error(setting, where, keys)
    for check in (type_error, label_error, choices_error):
        error = error or check(setting, where)
    return error


def keys_setting_names(settings: Any) -> set[str]:
    objects = [to_object(setting) for setting in to_array(settings)]
    return {string_at(item, "key") for item in objects if string_at(item, "type") == "keys"}


def keys_setting_error(item: dict[str, Any], index: int, keys_names: set[str]) -> str:
    reference = item.get("keysSetting", UNDEFINED)
    if reference is UNDEFINED or (isinstance(reference, str) and reference in keys_names):
        return ""
    return manifest_error(f"action.items[{index}].keysSetting: must name a keys setting")


def action_item_error(item: dict[str, Any], index: int, ids: set[str]) -> str:
    item_id = string_at(item, "id")
    is_invalid = not item_id or item_id in ids or not string_at(item, "title")
    ids.add(item_id)
    if not is_invalid:
        return ""
    return manifest_error(f"action.items[{index}]: needs a unique id and a title")


def items_error(items: list[Any], keys_names: set[str]) -> str:
    ids: set[str] = set()
    for index, value in enumerate(items):
        item = to_object(value)
        error = action_item_error(item, index, ids) or keys_setting_error(item, index, keys_names)
        if error:
            return error
    return ""


def settings_error(settings: Any) -> str:
    if settings is not UNDEFINED and not isinstance(settings, list):
        return manifest_error("settings: must be a list")
    keys: set[str] = set()
    for index, value in enumerate(to_array(settings)):
        error = setting_error(to_object(value), index, keys)
        if error:
            return error
    return ""


def action_error(action: Any, settings: Any) -> str:
    if action is not UNDEFINED and not isinstance(action, dict):
        return manifest_error("action: must be an object")
    items = to_array(to_object(action).get("items"))
    return items_error(items, keys_setting_names(settings))
