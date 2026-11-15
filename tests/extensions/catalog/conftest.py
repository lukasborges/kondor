from collections.abc import Iterator

import pytest

from kondor.core.settings.settings import Settings


@pytest.fixture
def catalog_root(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp("catalog"))


@pytest.fixture
def auto_update_on(work: str) -> Iterator[None]:
    Settings.instance().setProperty("extensionsAutoUpdate", True)
    yield
