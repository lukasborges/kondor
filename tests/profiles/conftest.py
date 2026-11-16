from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.registry.registrystore import open_registry
from kondor.profiles.userprofile import DEFAULT_ID


def clear_registry() -> None:
    settings: QSettings = open_registry()
    settings.clear()
    settings.sync()
    Path(settings.fileName()).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_registry(qapp: object) -> Iterator[None]:
    clear_registry()
    ActiveProfile.select(DEFAULT_ID)
    yield
    clear_registry()
    ActiveProfile.select(DEFAULT_ID)
