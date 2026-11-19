from PySide6.QtCore import QUrl

from kondor.translate.languagenames import language_name

BYTES_PER_MEGABYTE = 1_000_000
STATE_IDLE = "idle"
STATE_DOWNLOADING = "downloading"
STATE_TRANSLATING = "translating"
STATE_TRANSLATED = "translated"
STATE_ERROR = "error"
BUSY_STATES = (STATE_DOWNLOADING, STATE_TRANSLATING)
PAGE_STATE_TRANSLATED = "translated"
PAGE_STATE_ERROR = "error"


def web_host(url: QUrl) -> str:
    return url.host().lower() if url.scheme() in ("http", "https") else ""


def megabytes(byte_count: int) -> int:
    return byte_count // BYTES_PER_MEGABYTE


def progress_fraction(done: int, total: int) -> float:
    return min(1.0, done / total) if total > 0 else 0.0


def pair_label(source: str, target: str) -> str:
    return f"{language_name(source)} → {language_name(target)}"


def is_offerable(page_language: str, target: str, is_allowed: bool) -> bool:
    return bool(page_language) and page_language != target and is_allowed
