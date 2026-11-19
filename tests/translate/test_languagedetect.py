import pytest

from kondor.translate.page.languagedetect import (
    declared_language,
    detect_language,
    page_language,
    primary_subtag,
)


@pytest.mark.parametrize("tag, expected", [("en-US", "en"), ("PT_br", "pt"), ("de", "de")])
def test_reduces_a_language_tag_to_its_primary_subtag(tag: str, expected: str) -> None:
    assert primary_subtag(tag) == expected


@pytest.mark.parametrize("tag", ["", "und", "UND", "  "])
def test_an_empty_or_undetermined_tag_is_not_a_language(tag: str) -> None:
    assert declared_language(tag) is None


def test_the_declared_language_wins_over_detection() -> None:
    assert page_language("fr-CA", "This text is clearly written in English, as it happens.") == "fr"


def test_short_samples_are_not_detected() -> None:
    assert detect_language("hi") is None


def test_detects_the_language_of_a_page_without_a_lang_attribute() -> None:
    pytest.importorskip("langdetect")
    sample = "Este é um texto escrito em português para que o detector reconheça a língua."
    assert page_language("", sample) == "pt"
