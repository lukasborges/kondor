from collections.abc import Iterator
from pathlib import Path

import pytest

from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import remove_every_extension


@pytest.fixture
def work(kondor_types: None, staged_resources: None, tmp_path: Path) -> Iterator[str]:
    ExtensionManager.instance().set_locale("en")
    yield str(tmp_path)
    remove_every_extension()
