from typing import Any, NamedTuple

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineContextMenuRequest

from kondor.core.settings.settings import Settings

Request = QWebEngineContextMenuRequest
SEPARATOR = "-"
SEARCH_PLACEHOLDER = "%SEARCH%"
SELECTED_TEXT = "some words"


class Case(NamedTuple):
    name: str
    request: dict[str, Any]
    items: list[str]


def media_type(kind: Request.MediaType) -> int:
    return int(kind.value)


MEDIA_FLAGS = Request.MediaFlag.MediaCanToggleControls.value | Request.MediaFlag.MediaControls.value
LINK = {"linkUrl": QUrl("https://link.example/")}
IMAGE = {"mediaType": media_type(Request.MediaType.MediaTypeImage)}
VIDEO = {
    "mediaType": media_type(Request.MediaType.MediaTypeVideo),
    "mediaFlags": Request.MediaFlag.MediaCanToggleControls.value
    | Request.MediaFlag.MediaControls.value,
}
SELECTION = {"selectedText": SELECTED_TEXT}
MISSPELLED_FIELD = {
    "isContentEditable": True,
    "misspelledWord": "helo",
    "spellCheckerSuggestions": ["hello"],
    "editFlags": int(Request.EditFlag.CanPaste.value),
}

INSPECT = [SEPARATOR, "Inspect Element"]
LINK_ITEMS = [
    "Open Link in New Tab",
    "Open Link in New Private Tab",
    SEPARATOR,
    "Copy Link Address",
    "Save Link As…",
]
IMAGE_ITEMS = ["Open Image in New Tab", "Save Image As…", "Copy Image", "Copy Image Address"]

CASES = [
    Case("link", LINK, LINK_ITEMS + INSPECT),
    Case("image", IMAGE, IMAGE_ITEMS + INSPECT),
    Case("linkAndImage", {**LINK, **IMAGE}, LINK_ITEMS + [SEPARATOR] + IMAGE_ITEMS + INSPECT),
    Case(
        "videoWithControls",
        VIDEO,
        ["Save Media As…", "Copy Media Address", SEPARATOR, "Show Controls", "Loop"] + INSPECT,
    ),
    Case("selection", SELECTION, ["Copy", SEARCH_PLACEHOLDER] + INSPECT),
    Case(
        "misspelledField",
        MISSPELLED_FIELD,
        ["hello", SEPARATOR, "Undo", "Redo", SEPARATOR, "Cut", "Copy", "Paste"]
        + ["Paste as Plain Text", "Select All"]
        + INSPECT,
    ),
    Case(
        "nothing",
        {},
        ["Back", "Forward", "Reload", SEPARATOR, "Save Page As…", "Print…"]
        + ["Take Screenshot…", "View Page Source"]
        + INSPECT,
    ),
]


def complete_request(given: dict[str, Any]) -> dict[str, Any]:
    request: dict[str, Any] = {
        "linkUrl": QUrl(),
        "mediaUrl": QUrl(),
        "mediaType": media_type(Request.MediaType.MediaTypeNone),
        "mediaFlags": 0,
        "editFlags": 0,
        "isContentEditable": False,
        "selectedText": "",
        "misspelledWord": "",
        "spellCheckerSuggestions": [],
    }
    return {**request, **given}


def search_item() -> str:
    engine = Settings.instance().searchEngineName()
    if not engine:
        return f"Search for “{SELECTED_TEXT}”"
    return f"Search {engine} for “{SELECTED_TEXT}”"
