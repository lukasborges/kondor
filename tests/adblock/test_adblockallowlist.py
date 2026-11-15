from collections.abc import Iterator

import pytest

from kondor.adblock import adblocksettings
from kondor.adblock.adblockmanager import AdBlockManager

HOST = "example.org"


@pytest.fixture
def manager(qapp: object) -> Iterator[AdBlockManager]:
    manager = AdBlockManager.instance()
    adblocksettings.set_allow_list([])
    manager.setAllowed(HOST, False, False)
    manager.setAllowed(HOST, False, True)
    yield manager
    manager.setAllowed(HOST, False, False)
    manager.setAllowed(HOST, False, True)


def test_session_allow_does_not_touch_settings(manager: AdBlockManager) -> None:
    manager.setAllowed("Example.org", True, False)
    assert manager.isAllowed(HOST)
    assert adblocksettings.allow_list() == []


def test_session_block_overrides_the_persistent_list(manager: AdBlockManager) -> None:
    manager.setAllowed(HOST, True, True)
    manager.setAllowed(HOST, False, False)
    assert not manager.isAllowed(HOST)
    assert adblocksettings.allow_list() == [HOST]


def test_persistent_choice_replaces_the_session_choice(manager: AdBlockManager) -> None:
    manager.setAllowed(HOST, True, True)
    manager.setAllowed(HOST, False, False)
    manager.setAllowed(HOST, True, True)
    assert manager.isAllowed(HOST)
