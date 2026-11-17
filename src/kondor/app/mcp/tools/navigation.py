from kondor.app.mcp.cdp.pagesession import PageSession
from kondor.app.mcp.protocol.tool import PAGE_PROPERTY, Arguments, Tool, string_property
from kondor.app.mcp.protocol.toolresult import ToolFailureError, ToolResult, text_result
from kondor.app.mcp.tools.browser import Browser

LOAD_TIMEOUT_MILLISECONDS = 30000
LOAD_EVENT = "Page.loadEventFired"


def navigate_and_wait(session: PageSession, method: str, params: dict[str, object]) -> ToolResult:
    session.call("Page.enable")
    session.clear_events()
    session.call(method, params)
    if not session.wait_for_event(LOAD_EVENT, LOAD_TIMEOUT_MILLISECONDS):
        raise ToolFailureError("The page did not finish loading in 30 seconds.")
    return text_result("Done.")


def navigate(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    return navigate_and_wait(session, "Page.navigate", {"url": arguments["url"]})


def reload(browser: Browser, arguments: Arguments) -> ToolResult:
    return navigate_and_wait(browser.page(arguments.get("page")), "Page.reload", {})


def go_to_history_entry(session: PageSession, offset: int) -> ToolResult:
    history = session.call("Page.getNavigationHistory")
    index = history["currentIndex"] + offset
    if not 0 <= index < len(history["entries"]):
        raise ToolFailureError("There is no such entry in the page history.")
    entry_id = history["entries"][index]["id"]
    return navigate_and_wait(session, "Page.navigateToHistoryEntry", {"entryId": entry_id})


def go_back(browser: Browser, arguments: Arguments) -> ToolResult:
    return go_to_history_entry(browser.page(arguments.get("page")), -1)


def go_forward(browser: Browser, arguments: Arguments) -> ToolResult:
    return go_to_history_entry(browser.page(arguments.get("page")), 1)


PAGE = {"page": PAGE_PROPERTY}

TOOLS = [
    Tool(
        "navigate",
        "Load a URL in a page and wait for it to finish loading.",
        {**PAGE, "url": string_property("The URL to load.")},
        ("url",),
        navigate,
    ),
    Tool("go_back", "Go back one entry in the page history.", PAGE, (), go_back),
    Tool("go_forward", "Go forward one entry in the page history.", PAGE, (), go_forward),
    Tool("reload", "Reload the page and wait for it to finish loading.", PAGE, (), reload),
]
