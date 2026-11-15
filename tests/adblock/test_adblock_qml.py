from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine

from kondor.adblock.adblockmanager import AdBlockManager
from tests.qmlsupport import captured_messages, error_text, load_component

HOST = "example.org"
SOURCE = """import QtQml
import Kondor

QtObject {
    property bool enabled: AdBlockManager.enabled
    property bool updating: AdBlockManager.updating
    property var lastUpdate: AdBlockManager.lastUpdate
    property int count: AdBlockManager.blockedCount("example.org")
    property bool allowed: {
        AdBlockManager.setAllowed("example.org", true)
        return AdBlockManager.isAllowed("example.org")
    }
}
"""


@pytest.fixture
def reset_allow_list(kondor_engine: QQmlEngine) -> Iterator[QQmlEngine]:
    yield kondor_engine
    AdBlockManager.instance().setAllowed(HOST, False, True)


def test_ad_block_manager_is_used_from_qml(reset_allow_list: QQmlEngine) -> None:
    component = load_component(reset_allow_list, SOURCE)
    with captured_messages() as messages:
        created = component.create()
    assert created is not None, error_text(component)
    assert messages == []
    assert created.property("allowed") is True
    assert created.property("enabled") is True
    assert created.property("updating") is False
    assert created.property("count") == 0
