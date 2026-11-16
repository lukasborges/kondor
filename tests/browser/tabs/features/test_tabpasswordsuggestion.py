from PySide6.QtCore import QRectF

from kondor.browser.tabs.features.tabpasswordsuggestion import TabPasswordSuggestion

RECT = QRectF(10, 20, 200, 30)


def test_shows_and_clears_the_field() -> None:
    suggestion = TabPasswordSuggestion(False)
    suggestion.show_field("new", True, RECT)
    assert (suggestion.fieldKind, suggestion.isOffered, suggestion.fieldRect) == ("new", True, RECT)
    suggestion.clear_field()
    assert (suggestion.fieldKind, suggestion.isOffered) == ("", False)


def test_dismiss_keeps_the_field_but_withdraws_the_offer() -> None:
    suggestion = TabPasswordSuggestion(False)
    suggestion.show_field("new", True, RECT)
    suggestion.dismiss()
    assert (suggestion.fieldKind, suggestion.isOffered) == ("new", False)


def test_generate_requests_the_page_and_withdraws_the_offer() -> None:
    suggestion = TabPasswordSuggestion(False)
    requests: list[bool] = []
    suggestion.generateRequested.connect(lambda: requests.append(True))
    suggestion.show_field("new", True, RECT)
    suggestion.generate()
    assert requests == [True]
    assert suggestion.isOffered is False


def test_generated_password_is_taken_once() -> None:
    suggestion = TabPasswordSuggestion(False)
    suggestion.remember_generated("https://a.example", "secret")
    assert suggestion.take_generated("https://a.example", "other") is False
    assert suggestion.take_generated("https://a.example", "secret") is True
    assert suggestion.take_generated("https://a.example", "secret") is False


def test_private_tab_stays_empty() -> None:
    suggestion = TabPasswordSuggestion(True)
    suggestion.show_field("new", True, RECT)
    suggestion.remember_generated("https://a.example", "secret")
    assert (suggestion.fieldKind, suggestion.isOffered) == ("", False)
    assert suggestion.take_generated("https://a.example", "secret") is False
