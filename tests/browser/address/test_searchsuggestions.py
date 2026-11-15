from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkRequest
from pytestqt.qtbot import QtBot

from kondor.browser.address.searchsuggestions import SearchSuggestions, endpoint_url
from kondor.core.settings.settings import Settings
from tests.browser.address.fakenetwork import FakeNetworkAccessManager, settle_replies

QUIET_PERIOD_MS = 200


def encoded(url: QUrl) -> str:
    return str(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))


@pytest.fixture
def search_engine(qapp: object) -> Iterator[Settings]:
    settings = Settings.instance()
    previous = settings.property("searchEngine")
    yield settings
    settings.setProperty("searchEngine", previous)


@pytest.fixture
def network(qapp: object) -> Iterator[FakeNetworkAccessManager]:
    yield FakeNetworkAccessManager()
    settle_replies()


@pytest.fixture
def suggestions(network: FakeNetworkAccessManager) -> Iterator[SearchSuggestions]:
    suggestions = SearchSuggestions(network)
    yield suggestions
    suggestions.cancel()


def test_endpoint_follows_the_search_engine(search_engine: Settings) -> None:
    search_engine.setProperty("searchEngine", "google")
    google = "https://suggestqueries.google.com/complete/search?client=firefox&q=kde%20plasma"
    assert encoded(endpoint_url("kde plasma")) == google
    search_engine.setProperty("searchEngine", "duckduckgo")
    duckduckgo = "https://duckduckgo.com/ac/?type=list&q=kde%20plasma"
    assert encoded(endpoint_url("kde plasma")) == duckduckgo


def test_request_sets_the_user_agent_and_redirect_policy(
    suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    suggestions.request("kde")
    request = network.requests[0]
    assert request.header(QNetworkRequest.KnownHeaders.UserAgentHeader) == "Kondor Browser"
    policy = request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute)
    assert policy == QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy


def test_reply_emits_the_parsed_suggestions(
    qtbot: QtBot, suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    network.answer_with('["kde",["kde plasma","kde neon"]]')
    with qtbot.waitSignal(suggestions.suggestionsReady) as blocker:
        suggestions.request(" kde ")
    assert blocker.args == ["kde", ["kde plasma", "kde neon"]]


def test_failed_reply_emits_an_empty_list(
    qtbot: QtBot, suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    network.answer_with_failure()
    with qtbot.waitSignal(suggestions.suggestionsReady) as blocker:
        suggestions.request("kde")
    assert blocker.args == ["kde", []]


def test_blank_text_sends_nothing_and_cancels(
    qtbot: QtBot, suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    network.answer_with('["kde",["kde plasma"]]')
    suggestions.request("kde")
    with qtbot.assertNotEmitted(suggestions.suggestionsReady, wait=QUIET_PERIOD_MS):
        suggestions.request("   ")
    assert len(network.requests) == 1


def test_cancel_without_a_request_is_harmless(
    suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    suggestions.cancel()
    assert network.requests == []


def test_reply_of_a_cancelled_request_is_ignored(
    qtbot: QtBot, suggestions: SearchSuggestions, network: FakeNetworkAccessManager
) -> None:
    network.answer_with('["kde",["kde plasma"]]')
    with qtbot.assertNotEmitted(suggestions.suggestionsReady, wait=QUIET_PERIOD_MS):
        suggestions.request("kde")
        suggestions.cancel()
