from typing import Any

from PySide6.QtCore import QUrl

from kondor.app.krunner.runnericons import fallback_icon, icon_data
from kondor.app.krunner.runnermatches import RunnerMatch

CATEGORY_RELEVANCE = {"tab": 100, "bookmark": 70, "history": 50}
MATCH_SIGNATURE = "a(sssida{sv})"


def host_and_port(url: QUrl) -> str:
    return f"{url.host()}:{url.port()}" if url.port() > 0 else str(url.host())


def display_string(url: QUrl) -> str:
    if not url.userInfo():
        return str(url.toDisplayString())
    without_user_info = QUrl(url)
    without_user_info.setAuthority(host_and_port(url))
    return str(without_user_info.toDisplayString())


def properties_of(match: RunnerMatch) -> dict[str, tuple[str, Any]]:
    properties: dict[str, tuple[str, Any]] = {
        "subtext": ("s", display_string(match.url)),
        "urls": ("as", [match.url.toString()]),
        "actions": ("as", []),
    }
    data = icon_data(match.url)
    if data is not None:
        properties["icon-data"] = ("(iiibiiay)", data)
    return properties


def icon_name_of(match: RunnerMatch) -> str:
    return "" if icon_data(match.url) is not None else fallback_icon(match.kind)


def position_of(match: RunnerMatch) -> int:
    return int(match.match_id.rsplit("-", 1)[1])


def struct_of(match: RunnerMatch) -> tuple[Any, ...]:
    return (
        match.match_id,
        match.title or display_string(match.url),
        icon_name_of(match),
        CATEGORY_RELEVANCE[match.kind],
        1.0 - 0.01 * position_of(match),
        properties_of(match),
    )


def match_reply(matches: list[RunnerMatch]) -> tuple[str, tuple[Any, ...]]:
    return MATCH_SIGNATURE, ([struct_of(match) for match in matches],)
