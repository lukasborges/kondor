from typing import Any

import pytest

from kondor.core.database.database import Database
from kondor.extensions.state import extensionstorage as storage


@pytest.fixture(autouse=True)
def clean_storage(qapp: object) -> None:
    assert Database.instance().is_valid()
    storage.remove_extension("one")
    storage.remove_extension("two")


def big_text(kibibytes: int, letter: str) -> str:
    return letter * (kibibytes * 1024)


VALUES = [1.5, "text", True, {"n": 1, "list": [1, 2]}, ["a"]]


@pytest.mark.parametrize("value", VALUES, ids=repr)
def test_values_keep_their_json_type(value: Any) -> None:
    assert storage.set_value("one", "k", value).is_written
    assert storage.value("one", "k") == value


def test_missing_value_is_null() -> None:
    assert storage.value("one", "missing") is None


def test_quota_counts_the_other_keys_only() -> None:
    assert storage.set_value("one", "a", big_text(600, "x")).is_written
    refused = storage.set_value("one", "b", big_text(600, "y"))
    assert not refused.is_written
    assert "full" in refused.error
    assert storage.set_value("one", "a", big_text(900, "z")).is_written
    assert storage.keys("one") == ["a"]


def test_remove_extension_keeps_other_extensions() -> None:
    assert storage.set_value("one", "k", 1).is_written
    other = 2
    assert storage.set_value("two", "k", other).is_written
    storage.remove_extension("one")
    assert storage.keys("one") == []
    assert storage.value("two", "k") == other
