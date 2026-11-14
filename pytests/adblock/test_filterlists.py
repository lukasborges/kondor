from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QDateTime

from kondor.adblock.lists.filterlists import (
    cached_filter_list_files,
    filter_cache_directory,
    is_cache_stale,
    parse_filter_lists,
)


@pytest.fixture
def cache_files(qapp: object) -> Iterator[list[Path]]:
    Path(filter_cache_directory()).mkdir(parents=True, exist_ok=True)
    files = [Path(path) for path in cached_filter_list_files()]
    yield files
    for file in files:
        file.unlink(missing_ok=True)


def test_cache_is_stale_without_an_update_or_a_file(cache_files: list[Path]) -> None:
    now = QDateTime.currentDateTime()
    assert is_cache_stale(QDateTime())
    cache_files[0].write_text("||a.com^\n")
    assert is_cache_stale(now)
    cache_files[1].write_text("||b.com^\n")
    assert not is_cache_stale(now)


def test_cache_is_stale_after_four_days(cache_files: list[Path]) -> None:
    for file in cache_files:
        file.write_text("||a.com^\n")
    assert not is_cache_stale(QDateTime.currentDateTime().addDays(-3))
    assert is_cache_stale(QDateTime.currentDateTime().addDays(-4))


def test_parse_skips_missing_files(tmp_path: Path) -> None:
    existing = tmp_path / "list.txt"
    rules = ["||a.com^", "||b.com^$script"]
    existing.write_text("\n".join(rules))
    engine = parse_filter_lists([str(existing), str(tmp_path / "missing.txt")])
    assert engine.rule_count() == len(rules)
