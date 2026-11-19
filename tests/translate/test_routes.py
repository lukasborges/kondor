from kondor.translate.catalog.routes import (
    can_translate,
    plan_route,
    source_languages,
    target_languages,
)

PAIRS = {("en", "pt"), ("pt", "en"), ("de", "en"), ("en", "de"), ("en", "es")}


def test_prefers_the_direct_pair() -> None:
    assert plan_route(PAIRS, "en", "pt") == [("en", "pt")]


def test_goes_through_english_when_there_is_no_direct_pair() -> None:
    assert plan_route(PAIRS, "de", "pt") == [("de", "en"), ("en", "pt")]


def test_finds_no_route_when_a_leg_is_missing() -> None:
    assert plan_route(PAIRS, "es", "pt") is None


def test_finds_no_route_from_a_language_to_itself() -> None:
    assert plan_route(PAIRS, "en", "en") is None


def test_lists_languages_that_can_be_translated_from_and_to() -> None:
    assert source_languages(PAIRS) == ["de", "en", "pt"]
    assert target_languages(PAIRS) == ["de", "en", "es", "pt"]
    assert can_translate(PAIRS, "pt", "de")
