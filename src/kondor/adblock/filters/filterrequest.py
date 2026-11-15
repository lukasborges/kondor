from dataclasses import dataclass

from PySide6.QtCore import QUrl

from kondor.adblock.filters.filterkinds import ResourceKind
from kondor.adblock.filters.filterpattern import registrable_domain

SCHEME_SEPARATOR = "://"
URL_FORMAT = QUrl.ComponentFormattingOption.FullyEncoded | QUrl.UrlFormattingOption.RemoveFragment


@dataclass(slots=True)
class FilterRequest:
    url: str
    rest: str
    host: str
    first_party_host: str
    third_party: bool
    kind: int


def is_third_party(host: str, first_party_host: str) -> bool:
    if not first_party_host:
        return False
    return registrable_domain(host) != registrable_domain(first_party_host)


def text_after_host(url: str, host: str) -> str:
    host_start = url.find(SCHEME_SEPARATOR) + len(SCHEME_SEPARATOR)
    host_position = url.find(host, host_start)
    if host_position < 0:
        return ""
    return url[host_position + len(host) :]


def make_filter_request(url: QUrl, first_party_host: str, kind: ResourceKind) -> FilterRequest:
    text = url.toString(URL_FORMAT).lower()
    host = url.host().lower()
    first_party = first_party_host.lower()
    third_party = is_third_party(host, first_party)
    rest = text_after_host(text, host)
    return FilterRequest(text, rest, host, first_party, third_party, int(kind))
