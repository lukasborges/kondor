from dataclasses import dataclass
from typing import Any

from kondor.extensions.manifest.jsonvalue import UNDEFINED, to_string


@dataclass
class StringListField:
    key: str
    path: str = ""
    is_required: bool = False

    def label(self) -> str:
        return f"{self.path}.{self.key}" if self.path else self.key


def missing_list(field: StringListField) -> tuple[list[str] | None, str]:
    if not field.is_required:
        return [], ""
    return None, f"manifest.json: {field.label()}: required"


def read_strings(array: list[Any], field: StringListField) -> tuple[list[str] | None, str]:
    strings: list[str] = []
    for index, item in enumerate(array):
        strings.append(to_string(item))
        if not strings[-1]:
            message = f"manifest.json: {field.label()}[{index}]: must be a non-empty string"
            return None, message
    return strings, ""


def read_string_list(
    source: dict[str, Any], field: StringListField
) -> tuple[list[str] | None, str]:
    value = source.get(field.key, UNDEFINED)
    if value is UNDEFINED or value is None:
        return missing_list(field)
    if isinstance(value, list):
        return read_strings(value, field)
    return None, f"manifest.json: {field.label()}: must be a list of strings"
