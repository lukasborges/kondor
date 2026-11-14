from typing import Any

from PySide6.QtCore import QLocale

from kondor.extensions.manifest.jsonvalue import string_at, to_array, to_bool, to_object


def locale_candidates(locale: str) -> list[str]:
    name = locale or QLocale.system().name()
    return [name, name.split("_")[0]]


def localized(source: dict[str, Any], key: str, locale: str = "") -> str:
    for candidate in locale_candidates(locale):
        value = source.get(f"{key}[{candidate}]")
        if isinstance(value, str) and value:
            return value
    return string_at(source, key)


def localized_choice(choice: dict[str, Any], locale: str) -> dict[str, Any]:
    return {"value": choice.get("value"), "label": localized(choice, "label", locale)}


def localized_choices(choices: list[Any], locale: str) -> list[dict[str, Any]]:
    return [localized_choice(to_object(choice), locale) for choice in choices]


def localized_setting(setting: dict[str, Any], locale: str) -> dict[str, Any]:
    result = dict(setting)
    result["label"] = localized(setting, "label", locale)
    choices = to_array(setting.get("choices"))
    if choices:
        result["choices"] = localized_choices(choices, locale)
    return result


def localized_action_item(item: dict[str, Any], locale: str) -> dict[str, Any]:
    return {
        "id": string_at(item, "id"),
        "title": localized(item, "title", locale),
        "checkable": to_bool(item.get("checkable")),
        "icon": string_at(item, "icon"),
        "keysSetting": string_at(item, "keysSetting"),
    }


def settings_schema(manifest: dict[str, Any], locale: str = "") -> list[dict[str, Any]]:
    settings = to_array(manifest.get("settings"))
    return [localized_setting(to_object(setting), locale) for setting in settings]


def setting_defaults(manifest: dict[str, Any]) -> dict[str, Any]:
    settings = [to_object(setting) for setting in to_array(manifest.get("settings"))]
    return {string_at(setting, "key"): setting.get("default") for setting in settings}


def action_items(manifest: dict[str, Any], locale: str = "") -> list[dict[str, Any]]:
    items = to_array(to_object(manifest.get("action")).get("items"))
    return [localized_action_item(to_object(item), locale) for item in items]
