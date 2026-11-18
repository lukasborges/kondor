from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from kondor.app.mcp.protocol.jsonrpc import InvalidParamsError
from kondor.app.mcp.protocol.toolresult import ToolResult

Arguments = dict[str, Any]
Handler = Callable[[Any, Arguments], ToolResult]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    properties: dict[str, Any]
    required: tuple[str, ...]
    handler: Handler

    def definition(self) -> dict[str, Any]:
        schema = {"type": "object", "properties": self.properties, "required": list(self.required)}
        return {"name": self.name, "description": self.description, "inputSchema": schema}

    def check(self, arguments: Arguments) -> None:
        for name in self.required:
            if name not in arguments:
                raise InvalidParamsError(f"missing argument: {name}")
        for name, value in arguments.items():
            self.check_type(name, value)

    def check_type(self, name: str, value: object) -> None:
        expected = self.properties.get(name, {}).get("type")
        if expected is not None and not matches_type(expected, value):
            raise InvalidParamsError(f"argument {name} must be of type {expected}")


def matches_type(expected: str, value: object) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def string_property(description: str) -> dict[str, str]:
    return {"type": "string", "description": description}


PAGE_PROPERTY = string_property(
    "Page id from list_pages; defaults to the tab you used last. "
    "Only tabs open to agents work: open one with new_tab first."
)
UID_PROPERTY = string_property("Element uid from the latest snapshot.")
