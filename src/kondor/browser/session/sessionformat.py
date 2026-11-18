from typing import Any

from PySide6.QtCore import QJsonDocument, QJsonParseError, QUrl, qWarning

from kondor.browser.session.sessionwindow import SessionTab, SessionWindow

SESSION_VERSION = 2
FIRST_SESSION_VERSION = 1
NEW_TAB_PAGE_URL = "about:newtab"
JsonObject = dict[str, Any]


def json_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    return int(value) if float(value).is_integer() else 0


def json_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def json_object(value: object) -> JsonObject:
    return value if isinstance(value, dict) else {}


def json_array(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def tab_to_json(tab: SessionTab) -> JsonObject:
    url = NEW_TAB_PAGE_URL if tab.url.isEmpty() else tab.url.toString()
    entry: JsonObject = {"url": url, "title": tab.title}
    if tab.has_agent_access:
        entry.update({"agentAccess": True, "agentName": tab.agent_name})
    return entry


def window_to_json(window: SessionWindow) -> JsonObject:
    tabs = [tab_to_json(tab) for tab in window.tabs]
    return {"currentIndex": window.current_index, "tabs": tabs}


def to_json(windows: list[SessionWindow]) -> bytes:
    windows_json = [window_to_json(window) for window in windows]
    root = {"version": SESSION_VERSION, "windows": windows_json}
    document = QJsonDocument.fromVariant(root)
    return bytes(document.toJson(QJsonDocument.JsonFormat.Compact).data())


def tab_from_json(entry: JsonObject) -> SessionTab:
    url_text = json_text(entry.get("url"))
    url = QUrl() if url_text == NEW_TAB_PAGE_URL else QUrl(url_text)
    has_access = entry.get("agentAccess") is True
    name = json_text(entry.get("agentName")) if has_access else ""
    return SessionTab(url, json_text(entry.get("title")), has_access, name)


def window_from_json(entry: JsonObject) -> SessionWindow:
    tabs = [tab_from_json(json_object(tab)) for tab in json_array(entry.get("tabs"))]
    return SessionWindow(tabs, json_int(entry.get("currentIndex")))


def parse_root(json: bytes) -> JsonObject | None:
    error = QJsonParseError()
    document = QJsonDocument.fromJson(json, error)
    if error.error == QJsonParseError.ParseError.NoError and document.isObject():
        return json_object(document.object())
    qWarning(f"Kondor: ignoring invalid session file: {error.errorString()}")
    return None


def is_supported_version(root: JsonObject) -> bool:
    version = json_int(root.get("version"))
    if FIRST_SESSION_VERSION <= version <= SESSION_VERSION:
        return True
    qWarning("Kondor: ignoring unsupported session file version")
    return False


def window_entries(root: JsonObject) -> list[JsonObject]:
    if json_int(root.get("version")) < SESSION_VERSION:
        return [root]
    return [json_object(entry) for entry in json_array(root.get("windows"))]


def from_json(json: bytes) -> list[SessionWindow]:
    root = parse_root(json)
    if root is None or not is_supported_version(root):
        return []
    windows = [window_from_json(entry) for entry in window_entries(root)]
    return [window for window in windows if window.tabs]
