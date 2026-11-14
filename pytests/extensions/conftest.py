from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl

from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import remove_every_extension


@pytest.fixture
def work(kondor_types: None, staged_resources: None, tmp_path: Path) -> Iterator[str]:
    ExtensionManager.instance().set_locale("en")
    yield str(tmp_path)
    remove_every_extension()


@pytest.fixture(autouse=True)
def offline_catalog(work: str, tmp_path: Path) -> Iterator[None]:
    ExtensionCatalog.instance().set_catalog_url(QUrl.fromLocalFile(str(tmp_path / "none.json")))
    yield
    ExtensionCatalog.instance().set_catalog_url(QUrl())
