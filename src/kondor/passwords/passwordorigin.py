from PySide6.QtCore import QUrl

WEB_SCHEMES = ("http", "https")
DEFAULT_PORTS = {"http": 80, "https": 443}
NO_PORT = -1
LOCALHOST = "localhost"
SCHEME_SEPARATOR = "://"
SECURE_PREFIX = "https://"


def is_default_port(scheme: str, port: int) -> bool:
    return port in (NO_PORT, DEFAULT_PORTS[scheme])


def port_suffix(scheme: str, port: int) -> str:
    return "" if is_default_port(scheme, port) else f":{port}"


def is_localhost(host: str) -> bool:
    return host == LOCALHOST or host.endswith("." + LOCALHOST)


def encoded_host(url: QUrl) -> str:
    return str(url.host(QUrl.ComponentFormattingOption.FullyEncoded)).lower()


def origin_of(url: QUrl) -> str:
    scheme = url.scheme().lower()
    if scheme not in WEB_SCHEMES or not url.host():
        return ""
    return f"{scheme}{SCHEME_SEPARATOR}{encoded_host(url)}{port_suffix(scheme, url.port())}"


def can_save_for(origin: str) -> bool:
    url = QUrl(origin)
    host = encoded_host(url)
    if url.scheme() == "https":
        return bool(host)
    return url.scheme() == "http" and is_localhost(host)


def with_scheme(text: str) -> str:
    return text if SCHEME_SEPARATOR in text else SECURE_PREFIX + text


def origin_from_input(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    origin = origin_of(QUrl(with_scheme(stripped)))
    return origin if can_save_for(origin) else ""


def host_of_origin(origin: str) -> str:
    return str(QUrl(origin).host())
