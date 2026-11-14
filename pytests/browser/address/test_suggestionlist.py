from kondor.browser.address.suggestionlist import suggestions_from_json


def test_keeps_at_most_six_suggestions() -> None:
    items = suggestions_from_json(b'["q",["a","b","c","d","e","f","g","h"]]')
    assert items == ["a", "b", "c", "d", "e", "f"]


def test_skips_empty_and_non_string_entries() -> None:
    assert suggestions_from_json(b'["q",["a","",1,null,"b"]]') == ["a", "b"]


def test_returns_nothing_for_unexpected_json() -> None:
    assert suggestions_from_json(b"not json") == []
    assert suggestions_from_json(b'{"a":1}') == []
    assert suggestions_from_json(b'["q"]') == []
    assert suggestions_from_json(b'["q","text"]') == []
