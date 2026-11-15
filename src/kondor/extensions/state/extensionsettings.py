from collections.abc import Callable
from typing import Any

from kondor.extensions.manifest.jsonvalue import to_array, to_object


def fallback_of(setting: dict[str, Any]) -> Any:
    return setting.get("default")


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def number_of(value: Any) -> float | None:
    if is_number(value):
        return float(value)
    try:
        return float(value) if isinstance(value, str) else None
    except ValueError:
        return None


def clamped_number(setting: dict[str, Any], number: float) -> float:
    if "min" in setting:
        number = max(number, float(setting["min"]))
    if "max" in setting:
        number = min(number, float(setting["max"]))
    return number


def sanitize_bool(setting: dict[str, Any], value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if value in ("true", "false"):
        return value == "true"
    return bool(fallback_of(setting))


def sanitize_number(setting: dict[str, Any], value: Any) -> Any:
    number = number_of(value)
    return fallback_of(setting) if number is None else clamped_number(setting, number)


def offers_choice(choices: list[Any], value: Any) -> bool:
    return any(to_object(choice).get("value") == value for choice in choices)


def sanitize_choice(setting: dict[str, Any], value: Any) -> Any:
    choices = to_array(setting.get("choices"))
    return value if offers_choice(choices, value) else fallback_of(setting)


def sanitize_string(setting: dict[str, Any], value: Any) -> Any:
    return value if isinstance(value, str) else fallback_of(setting)


SANITIZERS: dict[str, Callable[[dict[str, Any], Any], Any]] = {
    "bool": sanitize_bool,
    "number": sanitize_number,
    "choice": sanitize_choice,
}


def sanitize_setting(setting: dict[str, Any], value: Any) -> Any:
    setting_type = setting.get("type")
    sanitize = SANITIZERS.get(str(setting_type), sanitize_string)
    return sanitize(setting, value)
