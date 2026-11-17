import json
from typing import Any

from kondor.app.mcp.protocol.tool import PAGE_PROPERTY, Arguments, Tool, string_property
from kondor.app.mcp.protocol.toolresult import ToolResult, error_result, image_result, text_result
from kondor.app.mcp.tools.browser import Browser
from kondor.app.mcp.tools.isolatedworld import run_in_world
from kondor.app.mcp.tools.snapshotscript import SNAPSHOT_SCRIPT

PAGE = {"page": PAGE_PROPERTY}


def snapshot(browser: Browser, arguments: Arguments) -> ToolResult:
    return text_result(str(run_in_world(browser.page(arguments.get("page")), SNAPSHOT_SCRIPT)))


def screenshot(browser: Browser, arguments: Arguments) -> ToolResult:
    reply = browser.page(arguments.get("page")).call("Page.captureScreenshot", {"format": "png"})
    return image_result(reply["data"], "image/png")


def evaluate(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    reply = session.call(
        "Runtime.evaluate",
        {"expression": arguments["expression"], "returnByValue": True, "awaitPromise": True},
    )
    if "exceptionDetails" in reply:
        return error_result(exception_text(reply["exceptionDetails"]))
    return text_result(json.dumps(reply.get("result", {}).get("value"), indent=2))


def exception_text(details: dict[str, Any]) -> str:
    description = details.get("exception", {}).get("description")
    return str(description or details.get("text", "The expression failed."))


TOOLS = [
    Tool(
        "snapshot",
        "Read the visible text of a page and a numbered list of its interactive elements (uid).",
        PAGE,
        (),
        snapshot,
    ),
    Tool("screenshot", "Take a PNG screenshot of the page.", PAGE, (), screenshot),
    Tool(
        "evaluate",
        "Evaluate a JavaScript expression in the page and return its JSON value.",
        {**PAGE, "expression": string_property("The JavaScript expression.")},
        ("expression",),
        evaluate,
    ),
]
