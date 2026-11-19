from kondor.translate.catalog.selection import select_engine, select_models
from tests.translate.recordfactory import engine_record, model_record, pair_records


def test_picks_the_newest_engine_with_the_vendored_major_version() -> None:
    records = [
        engine_record("2.0"),
        engine_record("3.0"),
        engine_record("3.1"),
        engine_record("4.0"),
    ]
    engine = select_engine(records)
    assert engine is not None
    assert engine.version == (3, 1)


def test_finds_no_engine_when_no_record_matches_the_major_version() -> None:
    assert select_engine([engine_record("2.0"), engine_record("4.0")]) is None


def test_skips_engine_records_with_a_filter_expression() -> None:
    assert select_engine([engine_record("3.0", "env.version|versionCompare('142') >= 0")]) is None


def test_picks_the_newest_supported_model_files_per_pair() -> None:
    records = pair_records("en", "pt", "1.0") + pair_records("en", "pt", "2.1")
    files = select_models(records)[("en", "pt")]
    assert {kind: file.version for kind, file in files.items()} == {
        "model": (2, 1),
        "lex": (2, 1),
        "vocab": (2, 1),
    }


def test_ignores_model_versions_the_engine_does_not_support() -> None:
    assert select_models(pair_records("en", "pt", "3.0")) == {}


def test_ignores_pre_release_and_filtered_model_records() -> None:
    records = [
        model_record(("en", "pt"), "model", "2.0a1"),
        {**model_record(("en", "pt"), "lex", "2.0"), "filter_expression": "x"},
    ]
    assert select_models(records) == {}


def test_drops_pairs_missing_a_required_file() -> None:
    records = [
        model_record(("en", "pt"), "model", "2.0"),
        model_record(("en", "pt"), "vocab", "2.0"),
    ]
    assert select_models(records) == {}


def test_accepts_separate_source_and_target_vocabularies() -> None:
    records = [
        model_record(("en", "ja"), kind, "2.0") for kind in ("model", "lex", "srcvocab", "trgvocab")
    ]
    assert ("en", "ja") in select_models(records)
