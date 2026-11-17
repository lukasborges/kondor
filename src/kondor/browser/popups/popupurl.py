from PySide6.QtCore import QUrl

BLANK_PAGE = "about:blank"
WEB_SCHEMES = ("http", "https")
MAX_URL_LENGTH = 2048


def is_web_address(url: QUrl) -> bool:
    return url.isValid() and url.scheme() in WEB_SCHEMES and bool(url.host())


def is_reportable(text: str) -> bool:
    return text == BLANK_PAGE or is_web_address(QUrl(text))


def parse_blocked_url(text: object) -> str | None:
    if not isinstance(text, str) or len(text) > MAX_URL_LENGTH:
        return None
    return text.strip() if is_reportable(text.strip()) else None
