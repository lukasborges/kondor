import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExtensionCall:
    extension_id: str = ""
    token: str = ""
    method: str = ""
    arguments: list[Any] = field(default_factory=list)


def parse_request_object(request_json: str) -> dict[str, Any]:
    try:
        request = json.loads(request_json)
    except ValueError:
        return {}
    return request if isinstance(request, dict) else {}


def text_field(request: dict[str, Any], name: str) -> str:
    value = request.get(name)
    return value if isinstance(value, str) else ""


def parse_extension_call(request_json: str) -> ExtensionCall:
    request = parse_request_object(request_json)
    arguments = request.get("arguments")
    return ExtensionCall(
        extension_id=text_field(request, "id"),
        token=text_field(request, "token"),
        method=text_field(request, "method"),
        arguments=arguments if isinstance(arguments, list) else [],
    )


def argument(call: ExtensionCall, index: int) -> Any:
    return call.arguments[index] if index < len(call.arguments) else None


def string_argument(call: ExtensionCall, index: int) -> str:
    value = argument(call, index)
    return value if isinstance(value, str) else ""


def bool_argument(call: ExtensionCall, index: int) -> bool:
    return argument(call, index) is True


def integral_floats_as_integers(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [integral_floats_as_integers(item) for item in value]
    if isinstance(value, dict):
        return {key: integral_floats_as_integers(item) for key, item in value.items()}
    return value


def compact(reply: dict[str, Any]) -> str:
    return json.dumps(
        integral_floats_as_integers(reply),
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    )


def ok_reply(value: Any = None) -> str:
    return compact({"ok": True, "value": value})


def error_reply(message: str) -> str:
    return compact({"ok": False, "error": message})
