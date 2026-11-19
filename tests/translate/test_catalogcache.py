import json
from pathlib import Path

from kondor.translate.download.catalogloader import RawCatalog
from kondor.translate.storage.catalogcache import CACHE_SECONDS, is_fresh, load_cached, write_cache
from tests.translate.recordfactory import engine_record, pair_records


def raw_catalog() -> RawCatalog:
    return RawCatalog([engine_record("3.0")], pair_records("en", "pt"), "https://cdn.example/")


def test_a_written_catalog_is_read_back_as_fresh(tmp_path: Path) -> None:
    write_cache(tmp_path / "catalog.json", raw_catalog())
    cached = load_cached(tmp_path / "catalog.json")
    assert cached.is_fresh
    assert cached.catalog is not None
    assert ("en", "pt") in cached.catalog.models


def test_a_missing_or_broken_cache_gives_no_catalog(tmp_path: Path) -> None:
    assert load_cached(tmp_path / "missing.json").catalog is None
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    assert load_cached(tmp_path / "broken.json").catalog is None


def test_a_cache_without_a_base_url_gives_no_catalog(tmp_path: Path) -> None:
    (tmp_path / "old.json").write_text(json.dumps({"saved": 1, "engine": [], "models": []}))
    assert load_cached(tmp_path / "old.json").catalog is None


def test_a_cache_older_than_a_day_is_stale() -> None:
    assert is_fresh(1000.0, 1000.0 + CACHE_SECONDS - 1)
    assert not is_fresh(1000.0, 1000.0 + CACHE_SECONDS)
    assert not is_fresh("yesterday", 1000.0)
