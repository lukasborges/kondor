from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from tests.browser.tabstrip.tabstripharness import TabStripHarness


@pytest.fixture
def strip(
    kondor_engine: QQmlEngine, desktop_style: None, qtbot: QtBot
) -> Iterator[TabStripHarness]:
    harness = TabStripHarness(kondor_engine, qtbot)
    yield harness
    harness.close()
