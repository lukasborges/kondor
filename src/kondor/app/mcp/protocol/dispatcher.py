from collections.abc import Callable

from kondor.app.mcp.protocol import jsonrpc
from kondor.app.mcp.protocol.jsonrpc import InvalidParamsError, JsonObject
from kondor.app.mcp.protocol.tool import Tool
from kondor.app.mcp.protocol.toolresult import ToolFailureError, ToolResult, error_result

KNOWN_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
LATEST_VERSION = KNOWN_VERSIONS[0]
Notify = Callable[[str, str], None]


class Dispatcher:
    def __init__(self, tools: list[Tool], context: object, version: str) -> None:
        self._tools = {tool.name: tool for tool in tools}
        self._context = context
        self._version = version
        self.on_client_known: Notify = lambda name, version: None

    def handle(self, message: JsonObject) -> JsonObject | None:
        request_id = message.get("id")
        method = message.get("method")
        if not isinstance(method, str):
            return jsonrpc.failure(request_id, jsonrpc.INVALID_REQUEST, "invalid request")
        if "id" not in message:
            return None
        return self.answer(request_id, method, message.get("params"))

    def answer(self, request_id: object, method: str, params: object) -> JsonObject:
        handler = self.methods().get(method)
        if handler is None:
            return jsonrpc.failure(
                request_id, jsonrpc.METHOD_NOT_FOUND, f"unknown method: {method}"
            )
        try:
            return jsonrpc.success(request_id, handler(params if isinstance(params, dict) else {}))
        except InvalidParamsError as error:
            return jsonrpc.failure(request_id, jsonrpc.INVALID_PARAMS, str(error))

    def methods(self) -> dict[str, Callable[[JsonObject], JsonObject]]:
        return {
            "initialize": self.initialize,
            "ping": lambda params: {},
            "tools/list": self.list_tools,
            "tools/call": self.call_tool,
        }

    def initialize(self, params: JsonObject) -> JsonObject:
        self.remember_client(params.get("clientInfo"))
        requested = params.get("protocolVersion")
        version = requested if requested in KNOWN_VERSIONS else LATEST_VERSION
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "kondor", "version": self._version},
        }

    def remember_client(self, info: object) -> None:
        if not isinstance(info, dict):
            return
        self.on_client_known(str(info.get("name", "")), str(info.get("version", "")))

    def list_tools(self, params: JsonObject) -> JsonObject:
        return {"tools": [tool.definition() for tool in self._tools.values()]}

    def call_tool(self, params: JsonObject) -> ToolResult:
        tool = self._tools.get(str(params.get("name")))
        if tool is None:
            raise InvalidParamsError(f"unknown tool: {params.get('name')}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise InvalidParamsError("arguments must be an object")
        tool.check(arguments)
        return self.run(tool, arguments)

    def run(self, tool: Tool, arguments: JsonObject) -> ToolResult:
        try:
            return tool.handler(self._context, arguments)
        except ToolFailureError as error:
            return error_result(str(error))
