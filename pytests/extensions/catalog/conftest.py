from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl

from kondor.core.settings.settings import Settings
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog


@pytest.fixture
def catalog_root(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp("catalog"))


@pytest.fixture(autouse=True)
def offline_catalog(work: str, tmp_path: Path) -> Iterator[None]:
    ExtensionCatalog.instance().set_catalog_url(QUrl.fromLocalFile(str(tmp_path / "none.json")))
    yield
    ExtensionCatalog.instance().set_catalog_url(QUrl())


@pytest.fixture
def auto_update_on(work: str) -> Iterator[None]:
    Settings.instance().setProperty("extensionsAutoUpdate", True)
    yield
