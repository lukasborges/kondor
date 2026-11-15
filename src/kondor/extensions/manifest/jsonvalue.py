from typing import Any

UNDEFINED: Any = object()


def value_of(source: dict[str, Any], key: str) -> Any:
    return source.get(key, UNDEFINED)


def is_undefined(value: Any) -> bool:
    return value is UNDEFINED


def is_double(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def to_int(value: Any) -> int:
    if not is_double(value) or value != int(value):
        return 0
    return int(value)


def to_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def to_array(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def to_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def to_bool(value: Any) -> bool:
    return value if isinstance(value, bool) else False


def string_at(source: dict[str, Any], key: str) -> str:
    return to_string(source.get(key))
