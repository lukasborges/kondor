from collections.abc import Iterator
from pathlib import Path

import pytest

from kondor.core.database.database import Database, database_path


def recreate_database() -> Path:
    Database.reset_instance()
    path = Path(database_path())
    path.unlink(missing_ok=True)
    assert Database.instance().is_valid()
    return path


@pytest.fixture
def fresh_bookmarks(kondor_types: None) -> Iterator[Path]:
    yield recreate_database()
    Database.reset_instance()
