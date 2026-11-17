import pytest

from kondor.browser.popups.popupurl import MAX_URL_LENGTH, parse_blocked_url


@pytest.mark.parametrize("text", ["https://kde.org/a?b=1", "http://localhost:8080/", "about:blank"])
def test_accepts_web_addresses_and_the_blank_page(text: str) -> None:
    assert parse_blocked_url(text) == text


@pytest.mark.parametrize(
    "text", ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,x", "", "https://"]
)
def test_rejects_other_addresses(text: str) -> None:
    assert parse_blocked_url(text) is None


def test_rejects_values_that_are_not_text_or_are_too_long() -> None:
    assert parse_blocked_url(42) is None
    assert parse_blocked_url("https://kde.org/" + "a" * MAX_URL_LENGTH) is None
