import os
from pathlib import Path

import pytest

from kondor.app.startup import positioncache


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    return tmp_path / positioncache.CACHE_FILE_NAME


def test_creates_the_discarding_link(cache: Path) -> None:
    positioncache.discard_position_cache()

    assert os.readlink(cache) == "/dev/null"


def test_replaces_a_regular_file(cache: Path) -> None:
    cache.write_bytes(b"last position")

    positioncache.discard_position_cache()

    assert os.readlink(cache) == "/dev/null"


def test_leaves_a_correct_link_untouched(cache: Path) -> None:
    positioncache.discard_position_cache()
    first_inode = cache.lstat().st_ino

    positioncache.discard_position_cache()

    assert cache.lstat().st_ino == first_inode
