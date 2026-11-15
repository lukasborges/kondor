from PySide6.QtCore import QRegularExpression, QUrl

HOST_PATTERN = QRegularExpression(
    r"^(([0-9]{1,3}\.){3}[0-9]{1,3}|localhost|[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})"
    r"(:\d+)?(/.*)?$"
)
EXPLICIT_SCHEME_PREFIXES = ("about:", "data:")
OCTET_COUNT = 4
MAX_OCTET = 255
LOCAL_SCHEME = "http://"
SECURE_SCHEME = "https://"
SEARCH_PLACEHOLDER = "%1"
WHOLE_PRIVATE_NETWORKS = (127, 10)
HOME_NETWORK = (192, 168)
SHARED_NETWORK = 172
SHARED_NETWORK_SECOND_OCTETS = range(16, 32)


def parse_octet(text: str) -> int | None:
    if not text.isascii() or not text.isdigit():
        return None
    octet = int(text)
    return octet if octet <= MAX_OCTET else None


def parse_ipv4(host: str) -> list[int] | None:
    octets = [parse_octet(part) for part in host.split(".")]
    if len(octets) != OCTET_COUNT or None in octets:
        return None
    return [octet for octet in octets if octet is not None]


def is_private_range(octets: list[int]) -> bool:
    first, second = octets[0], octets[1]
    return (
        first in WHOLE_PRIVATE_NETWORKS
        or (first, second) == HOME_NETWORK
        or (first == SHARED_NETWORK and second in SHARED_NETWORK_SECOND_OCTETS)
    )


def is_local_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    octets = parse_ipv4(host)
    return octets is not None and is_private_range(octets)


def has_explicit_scheme(text: str) -> bool:
    return "://" in text or text.startswith(EXPLICIT_SCHEME_PREFIXES)


def url_for_host_pattern(text: str) -> QUrl:
    match = HOST_PATTERN.match(text)
    if not match.hasMatch():
        return QUrl()
    scheme = LOCAL_SCHEME if is_local_host(match.captured(1)) else SECURE_SCHEME
    return QUrl(scheme + text)


def address_url(text: str) -> QUrl:
    typed = text.strip()
    if not typed:
        return QUrl()
    if has_explicit_scheme(typed):
        return QUrl.fromUserInput(typed)
    return url_for_host_pattern(typed)


def search_url(text: str, search_template: str) -> QUrl:
    encoded = QUrl.toPercentEncoding(text.strip()).data().decode()
    return QUrl(search_template.replace(SEARCH_PLACEHOLDER, encoded))


def resolve_address(text: str, home_page: QUrl, search_template: str) -> QUrl:
    if not text.strip():
        return home_page
    url = address_url(text)
    return search_url(text, search_template) if url.isEmpty() else url
