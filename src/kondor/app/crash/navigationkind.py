from PySide6.QtCore import QUrl

SITE_LABELS = 2


def site_of(url: QUrl) -> str:
    labels = url.host().lower().split(".")
    return ".".join(labels[-SITE_LABELS:])


def navigation_kind(previous: QUrl, destination: QUrl) -> str:
    if previous.isEmpty() or site_of(previous) != site_of(destination):
        return "cross-site"
    return "same-site"
