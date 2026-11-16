import math
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QUrl

MAX_TEXT_LENGTH = 512
KNOWN_ACTIONS = frozenset({"play", "pause", "stop", "nexttrack", "previoustrack", "seekto"})
WEB_SCHEMES = ("http", "https")


@dataclass(frozen=True)
class MediaState:
    has_media: bool = False
    is_playing: bool = False
    title: str = ""
    artist: str = ""
    album: str = ""
    artwork_url: QUrl = field(default_factory=QUrl)
    duration: float = 0.0
    position: float = 0.0
    rate: float = 1.0
    actions: frozenset[str] = frozenset()
    was_seeked: bool = False


def text_of(value: Any) -> str:
    return value.strip()[:MAX_TEXT_LENGTH] if isinstance(value, str) else ""


def number_of(value: Any) -> float:
    is_number = isinstance(value, int | float) and not isinstance(value, bool)
    return float(value) if is_number and math.isfinite(value) and value >= 0 else 0.0


def rate_of(value: Any) -> float:
    rate = number_of(value)
    return rate if rate > 0 else 1.0


def artwork_of(value: Any) -> QUrl:
    url = QUrl(text_of(value))
    return url if url.isValid() and url.scheme() in WEB_SCHEMES else QUrl()


def actions_of(value: Any) -> frozenset[str]:
    names = value if isinstance(value, list) else []
    return frozenset(name for name in names if name in KNOWN_ACTIONS)


def text_fields(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": text_of(report.get("title")),
        "artist": text_of(report.get("artist")),
        "album": text_of(report.get("album")),
        "artwork_url": artwork_of(report.get("artworkUrl")),
    }


def playback_fields(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "is_playing": report.get("playing") is True,
        "duration": number_of(report.get("duration")),
        "position": number_of(report.get("position")),
        "rate": rate_of(report.get("rate")),
        "actions": actions_of(report.get("actions")),
        "was_seeked": report.get("seeked") is True,
    }


def parse_report(report: dict[str, Any]) -> MediaState:
    if report.get("hasMedia") is not True:
        return MediaState()
    return MediaState(has_media=True, **text_fields(report), **playback_fields(report))
