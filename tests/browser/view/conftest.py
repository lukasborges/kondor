from collections.abc import Iterator

import pytest

from tests.qmlsupport import drain_deferred_deletes


@pytest.fixture(autouse=True)
def drained_deferred_deletes(qapp: object) -> Iterator[None]:
    yield
    drain_deferred_deletes()
