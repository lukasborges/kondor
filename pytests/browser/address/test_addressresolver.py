import pytest
from PySide6.QtCore import QUrl

from kondor.browser.address.addressresolver import address_url, resolve_address, search_url

HOME_PAGE = "https://home.example/"
SEARCH_TEMPLATE = "https://duckduckgo.com/?q=%1"

RESOLVE_ROWS = {
    "empty input uses the home page": ("", HOME_PAGE),
    "blank input uses the home page": ("   ", HOME_PAGE),
    "naked domain": ("kde.org", "https://kde.org"),
    "domain with path": ("kde.org/applications", "https://kde.org/applications"),
    "explicit scheme": ("http://example.com", "http://example.com"),
    "localhost with port": ("localhost:8080", "http://localhost:8080"),
    "loopback ip": ("127.0.0.1", "http://127.0.0.1"),
    "private 10/8": ("10.0.0.1", "http://10.0.0.1"),
    "private 192.168/16": ("192.168.0.1", "http://192.168.0.1"),
    "private 172.16/12": ("172.16.0.1", "http://172.16.0.1"),
    "public 172.15": ("172.15.0.1", "https://172.15.0.1"),
    "public 172.32": ("172.32.0.1", "https://172.32.0.1"),
    "public ip": ("8.8.8.8", "https://8.8.8.8"),
    "about scheme": ("about:blank", "about:blank"),
    "file scheme": ("file:///etc/hosts", "file:///etc/hosts"),
    "data scheme": ("data:text/plain,hi", "data:text/plain,hi"),
    "single word searches": ("kde", "https://duckduckgo.com/?q=kde"),
    "spaces are encoded": ("hello world", "https://duckduckgo.com/?q=hello%20world"),
    "plus and space are encoded": (
        "c++ tutorial",
        "https://duckduckgo.com/?q=c%2B%2B%20tutorial",
    ),
    "question with a domain searches": (
        "what is kde.org?",
        "https://duckduckgo.com/?q=what%20is%20kde.org%3F",
    ),
}

ADDRESS_ROWS = {
    "naked domain": ("teste.com.br", "https://teste.com.br"),
    "domain with path": ("kde.org/applications", "https://kde.org/applications"),
    "explicit scheme": ("http://example.com", "http://example.com"),
    "node.js looks like a host": ("node.js", "https://node.js"),
    "localhost with port": ("localhost:8080", "http://localhost:8080"),
    "about scheme": ("about:blank", "about:blank"),
    "plain word is not an address": ("kde", ""),
    "spaces are not an address": ("kde plasma", ""),
    "blank input": ("", ""),
    "whitespace input": ("   ", ""),
}

SEARCH_ROWS = {
    "address text still has a search URL": (
        "teste.com.br",
        "https://duckduckgo.com/?q=teste.com.br",
    ),
    "node.js searches too": ("node.js", "https://duckduckgo.com/?q=node.js"),
    "plain words": ("kde plasma", "https://duckduckgo.com/?q=kde%20plasma"),
    "localhost": ("localhost:8080", "https://duckduckgo.com/?q=localhost%3A8080"),
    "blank input": ("", "https://duckduckgo.com/?q="),
}


def encoded(url: QUrl) -> str:
    return str(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))


@pytest.mark.parametrize(("text", "expected"), RESOLVE_ROWS.values(), ids=RESOLVE_ROWS.keys())
def test_resolves_address(text: str, expected: str) -> None:
    assert encoded(resolve_address(text, QUrl(HOME_PAGE), SEARCH_TEMPLATE)) == expected


@pytest.mark.parametrize(("text", "expected"), ADDRESS_ROWS.values(), ids=ADDRESS_ROWS.keys())
def test_address_urls(text: str, expected: str) -> None:
    assert encoded(address_url(text)) == expected


@pytest.mark.parametrize(("text", "expected"), SEARCH_ROWS.values(), ids=SEARCH_ROWS.keys())
def test_search_urls(text: str, expected: str) -> None:
    assert encoded(search_url(text, SEARCH_TEMPLATE)) == expected
