from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine, QQmlExpression, qmlContext
from pytestqt.qtbot import QtBot

from kondor.app.remotecontrol.connections.connection import Connection
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.app.remotecontrol.remotecontrol import RemoteControl
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

BUTTON_QML = """import QtQuick
import QtQuick.Controls
import Kondor
Item {
    width: 200; height: 100
    RemoteControlButton { objectName: "button"; browserWindow: null }
}
"""


def tooltip_of(button: QObject) -> object:
    expression = QQmlExpression(qmlContext(button), button, "describeConnections()")
    return expression.evaluate()[0]


@pytest.fixture
def connections(kondor_engine: QQmlEngine) -> Iterator[ConnectionModel]:
    model = RemoteControl.instance().connection_model()
    yield model
    while model.rowCount():
        model.remove(model._connections[0])


@pytest.fixture
def button(
    qtbot: QtBot, kondor_engine: QQmlEngine, connections: ConnectionModel
) -> Iterator[QObject]:
    component = load_component(kondor_engine, BUTTON_QML)
    root = component.create()
    assert root is not None, error_text(component)
    yield root.findChild(QObject, "button")
    root.deleteLater()


def test_is_hidden_while_nothing_is_connected(button: QObject) -> None:
    assert button.property("visible") is False


def test_appears_with_the_agent_name_while_it_is_connected(
    button: QObject, connections: ConnectionModel
) -> None:
    connections.add(Connection("Claude Code"))

    assert button.property("visible") is True
    assert tooltip_of(button) == "Claude Code is controlling Kondor"


def test_names_an_automation_tool_without_a_name(
    button: QObject, connections: ConnectionModel
) -> None:
    connections.add(Connection(""))

    assert tooltip_of(button) == "An automation tool is controlling Kondor"


def test_counts_agents_when_several_are_connected(
    button: QObject, connections: ConnectionModel
) -> None:
    connections.add(Connection("Claude Code"))
    connections.add(Connection("opencode"))

    assert tooltip_of(button) == "2 agents are controlling Kondor"


def test_hides_again_when_the_last_connection_goes_away(
    button: QObject, connections: ConnectionModel
) -> None:
    connections.add(Connection("Claude Code"))
    connections.remove(connections._connections[0])

    assert button.property("visible") is False
