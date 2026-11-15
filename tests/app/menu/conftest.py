from collections.abc import Iterator

import pytest
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlEngine

from tests.app.menu.mainmenuharness import MainMenuHarness, add_favicon_provider
from tests.app.menu.mainmenustub import STUB_WINDOW_QML


@pytest.fixture
def menu_engine(kondor_engine: QQmlEngine) -> QQmlEngine:
    add_favicon_provider(kondor_engine)
    return kondor_engine


@pytest.fixture
def menu(menu_engine: QQmlEngine) -> Iterator[MainMenuHarness]:
    harness = MainMenuHarness(menu_engine, STUB_WINDOW_QML)
    harness.show()
    yield harness
    harness.close()


@pytest.fixture
def accessibility() -> None:
    QAccessible.setActive(True)
