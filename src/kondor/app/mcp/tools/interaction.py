from kondor.app.mcp.protocol.tool import (
    PAGE_PROPERTY,
    UID_PROPERTY,
    Arguments,
    Tool,
    string_property,
)
from kondor.app.mcp.protocol.toolresult import ToolResult, text_result
from kondor.app.mcp.tools import keys, pointer
from kondor.app.mcp.tools.browser import Browser

DEFAULT_SCROLL_PIXELS = 300
DIRECTIONS = {"down": (0, 1), "up": (0, -1), "right": (1, 0), "left": (-1, 0)}
PAGE = {"page": PAGE_PROPERTY}
TARGET = {**PAGE, "uid": UID_PROPERTY}


def click(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    pointer.click_at(session, pointer.element_center(session, arguments["uid"]))
    return text_result("Clicked.")


def hover(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    pointer.move_to(session, pointer.element_center(session, arguments["uid"]))
    return text_result("Hovered.")


def type_text(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    pointer.click_at(session, pointer.element_center(session, arguments["uid"]))
    session.call("Input.insertText", {"text": arguments["text"]})
    if arguments.get("submit") is True:
        keys.press(session, "Enter")
    return text_result("Typed.")


def press_key(browser: Browser, arguments: Arguments) -> ToolResult:
    keys.press(browser.page(arguments.get("page")), arguments["key"])
    return text_result("Pressed.")


def scroll(browser: Browser, arguments: Arguments) -> ToolResult:
    session = browser.page(arguments.get("page"))
    direction = DIRECTIONS.get(arguments["direction"], DIRECTIONS["down"])
    amount = arguments.get("amount", DEFAULT_SCROLL_PIXELS)
    pointer.wheel(
        session, pointer.viewport_center(session), (direction[0] * amount, direction[1] * amount)
    )
    return text_result("Scrolled.")


TOOLS = [
    Tool("click", "Click an element with the mouse.", TARGET, ("uid",), click),
    Tool("hover", "Move the mouse over an element.", TARGET, ("uid",), hover),
    Tool(
        "type_text",
        "Click an element and type text into it.",
        {
            **TARGET,
            "text": string_property("The text to type."),
            "submit": {"type": "boolean", "description": "Press Enter afterwards."},
        },
        ("uid", "text"),
        type_text,
    ),
    Tool(
        "press_key",
        "Press a key such as Enter, Escape, Tab, ArrowDown or a combination like Ctrl+A.",
        {**PAGE, "key": string_property("The key or combination.")},
        ("key",),
        press_key,
    ),
    Tool(
        "scroll",
        "Scroll the page with the mouse wheel.",
        {
            **PAGE,
            "direction": {"type": "string", "enum": list(DIRECTIONS), "description": "Direction."},
            "amount": {"type": "integer", "description": "Pixels, 300 by default."},
        },
        ("direction",),
        scroll,
    ),
]
