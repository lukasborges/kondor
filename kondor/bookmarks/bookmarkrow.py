from dataclasses import dataclass

from PySide6.QtCore import QUrl

SUPPORTED_SCHEMES = ("http", "https", "file")


@dataclass(frozen=True)
class BookmarkRow:
    is_folder: bool
    title: str
    url: QUrl
    parent_id: int
    position: int


def is_supported_bookmark_url(url: QUrl) -> bool:
    return not url.isEmpty() and url.scheme() in SUPPORTED_SCHEMES
