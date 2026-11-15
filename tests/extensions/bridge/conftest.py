from collections.abc import Iterator

import pytest
from shiboken6 import delete, isValid

from tests.extensions.bridge.bridgeharness import BridgeFixture
from tests.extensions.extensionsharness import install_sample


@pytest.fixture
def fixture(work: str) -> Iterator[BridgeFixture]:
    assert install_sample(work)
    bridge_fixture = BridgeFixture()
    yield bridge_fixture
    for item in (bridge_fixture.bridge, bridge_fixture.tab):
        if isValid(item):
            delete(item)
