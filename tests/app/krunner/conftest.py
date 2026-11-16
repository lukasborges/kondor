from collections.abc import Iterator
from pathlib import Path

import pytest

from kondor.core.database.database import Database
from tests.bookmarks.conftest import recreate_database
from tests.history.historyrows import reset_history


@pytest.fixture
def fresh_database(qapp: object) -> Iterator[Path]:
    path = recreate_database()
    reset_history()
    yield path
    reset_history()
    Database.reset_instance()
