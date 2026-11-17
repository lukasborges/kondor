import json

from kondor.app.mcp.protocol.tool import Arguments, Tool, string_property
from kondor.app.mcp.protocol.toolresult import ToolResult, text_result
from kondor.app.mcp.tools.browser import Browser, PageInfo


def describe(page: PageInfo) -> dict[str, object]:
    return {"id": page.id, "title": page.title, "url": page.url, "current": page.is_current}


def list_pages(browser: Browser, arguments: Arguments) -> ToolResult:
    return text_result(json.dumps([describe(page) for page in browser.list_pages()], indent=2))


def new_tab(browser: Browser, arguments: Arguments) -> ToolResult:
    page = browser.open_tab(arguments["url"])
    return text_result(json.dumps(describe(page), indent=2))


TOOLS = [
    Tool(
        "list_pages",
        "List the open tabs: id, title, URL and which one is current.",
        {},
        (),
        list_pages,
    ),
    Tool(
        "new_tab",
        "Open a URL in a new tab of Kondor.",
        {"url": string_property("The URL to open.")},
        ("url",),
        new_tab,
    ),
]
