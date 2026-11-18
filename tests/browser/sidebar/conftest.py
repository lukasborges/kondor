from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine

from tests.browser.sidebar.sidebarharness import SideBarHarness


@pytest.fixture(params=[False, True], ids=["expanded", "collapsed"])
def side_bar(
    request: pytest.FixtureRequest, kondor_engine: QQmlEngine, desktop_style: None
) -> Iterator[SideBarHarness]:
    harness = SideBarHarness(kondor_engine, request.param)
    yield harness
    harness.close()
