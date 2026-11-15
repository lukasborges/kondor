from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from tests.extensions.panel.panelfixture import PanelFixture


@pytest.fixture
def panel(qtbot: QtBot, work: str, kondor_engine: QQmlEngine) -> Iterator[PanelFixture]:
    fixture = PanelFixture(qtbot, kondor_engine, work)
    yield fixture
    fixture.reset()
