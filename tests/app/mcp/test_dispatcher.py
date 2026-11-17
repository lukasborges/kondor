from typing import Any

from kondor.app.mcp.protocol.dispatcher import Dispatcher
from kondor.app.mcp.protocol.tool import Tool, string_property
from kondor.app.mcp.protocol.toolresult import ToolFailureError, ToolResult, text_result

INVALID_PARAMS = -32602
METHOD_NOT_FOUND = -32601


def echo(context: object, arguments: dict[str, Any]) -> ToolResult:
    return text_result(arguments["word"])


def fail(context: object, arguments: dict[str, Any]) -> ToolResult:
    raise ToolFailureError("no luck")


def make_dispatcher() -> Dispatcher:
    tools = [
        Tool("echo", "Echo.", {"word": string_property("A word.")}, ("word",), echo),
        Tool("fail", "Fails.", {}, (), fail),
    ]
    return Dispatcher(tools, None, "1.2.3")


def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}


def answer(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = make_dispatcher().handle(request(method, params))
    assert response is not None
    return response


def test_answers_the_protocol_version_it_knows() -> None:
    result = answer("initialize", {"protocolVersion": "2025-03-26"})["result"]

    assert result["protocolVersion"] == "2025-03-26"
    assert result["serverInfo"] == {"name": "kondor", "version": "1.2.3"}
    assert result["capabilities"] == {"tools": {}}


def test_answers_the_latest_version_for_an_unknown_one() -> None:
    result = answer("initialize", {"protocolVersion": "1999-01-01"})["result"]

    assert result["protocolVersion"] == "2025-06-18"


def test_reports_the_client_that_initialized() -> None:
    dispatcher = make_dispatcher()
    seen: list[tuple[str, str]] = []
    dispatcher.on_client_known = lambda name, version: seen.append((name, version))

    dispatcher.handle(
        request("initialize", {"clientInfo": {"name": "Claude Code", "version": "2"}})
    )

    assert seen == [("Claude Code", "2")]


def test_reports_the_title_of_the_client_when_it_has_one() -> None:
    dispatcher = make_dispatcher()
    seen: list[str] = []
    dispatcher.on_client_known = lambda name, version: seen.append(name)

    info = {"name": "claude-code", "title": "Claude Code", "version": "2"}
    dispatcher.handle(request("initialize", {"clientInfo": info}))

    assert seen == ["Claude Code"]


def test_reports_the_name_of_the_client_without_a_title() -> None:
    dispatcher = make_dispatcher()
    seen: list[str] = []
    dispatcher.on_client_known = lambda name, version: seen.append(name)

    dispatcher.handle(request("initialize", {"clientInfo": {"name": "tool", "title": ""}}))

    assert seen == ["tool"]


def test_answers_ping_with_an_empty_result() -> None:
    assert answer("ping")["result"] == {}


def test_does_not_answer_notifications() -> None:
    message = {"jsonrpc": "2.0", "method": "notifications/initialized"}

    assert make_dispatcher().handle(message) is None


def test_rejects_an_unknown_method() -> None:
    assert answer("nope")["error"]["code"] == METHOD_NOT_FOUND


def test_lists_tools_with_their_schema() -> None:
    tools = answer("tools/list")["result"]["tools"]

    assert [tool["name"] for tool in tools] == ["echo", "fail"]
    assert tools[0]["inputSchema"]["required"] == ["word"]


def test_calls_a_tool() -> None:
    result = answer("tools/call", {"name": "echo", "arguments": {"word": "hi"}})["result"]

    assert result["content"] == [{"type": "text", "text": "hi"}]


def test_rejects_a_missing_argument() -> None:
    response = answer("tools/call", {"name": "echo", "arguments": {}})

    assert response["error"]["code"] == INVALID_PARAMS


def test_rejects_an_argument_of_the_wrong_type() -> None:
    response = answer("tools/call", {"name": "echo", "arguments": {"word": 3}})

    assert response["error"]["code"] == INVALID_PARAMS


def test_rejects_an_unknown_tool() -> None:
    assert answer("tools/call", {"name": "nope"})["error"]["code"] == INVALID_PARAMS


def test_turns_a_tool_failure_into_an_error_result() -> None:
    result = answer("tools/call", {"name": "fail"})["result"]

    assert result["isError"] is True
    assert result["content"][0]["text"] == "no luck"
