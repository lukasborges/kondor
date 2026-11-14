from PySide6.QtCore import QUrl

from kondor.adblock.filters.filterengine import ResourceKind
from kondor.adblock.filters.filterpattern import url_tokens
from kondor.adblock.filters.filterrequest import make_filter_request


def test_drops_the_fragment_and_lower_cases() -> None:
    url = QUrl("https://Ads.Example.com/A.js?x=1#Frag")
    request = make_filter_request(url, "News.org", ResourceKind.SCRIPT)
    assert request.url == "https://ads.example.com/a.js?x=1"
    assert request.host == "ads.example.com"
    assert request.rest == "/a.js?x=1"
    assert request.first_party_host == "news.org"


def test_encodes_non_ascii_paths() -> None:
    url = QUrl("https://a.org/café.js")
    request = make_filter_request(url, "a.org", ResourceKind.SCRIPT)
    assert request.url == "https://a.org/caf%c3%a9.js"
    assert request.rest == "/caf%c3%a9.js"


def test_tokens_are_ascii_only() -> None:
    assert url_tokens("https://a.org/abcé123/xy") == {"https", "org", "abc", "123"}
