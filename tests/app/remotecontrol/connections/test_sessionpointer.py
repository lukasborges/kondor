import pytest
from PySide6.QtCore import QObject

from kondor.app.instance import sessionprotocol
from kondor.app.instance.sessionprotocol import RemoteControlState
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.app.remotecontrol.connections.sessionregistry import SessionRegistry
from kondor.browser.agent.agentpointer import AgentPointer
from kondor.browser.agent.agenttabs import AgentTabs
from kondor.browser.agent.tabagent import TabAgent
from tests.app.remotecontrol.connections.test_connections import FakeSocket, hello

pytestmark = pytest.mark.usefixtures("qapp")


class PointerLog(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.moves: list[tuple[str, float, float]] = []
        self.presses: list[tuple[str, float, float]] = []
        AgentPointer.instance().moved.connect(lambda *args: self.moves.append(args))
        AgentPointer.instance().pressed.connect(lambda *args: self.presses.append(args))


def parsed(line: bytes) -> dict[str, object]:
    return sessionprotocol.parse_object(line) or {}


def started_session() -> tuple[SessionRegistry, FakeSocket]:
    registry = SessionRegistry(ConnectionModel())
    registry.state = RemoteControlState(True, 9222)
    socket = FakeSocket()
    registry.handle_line(socket, hello("Claude Code"))
    return registry, socket


def test_shows_the_pointer_of_a_registered_session() -> None:
    registry, socket = started_session()
    log = PointerLog()

    registry.handle_line(socket, parsed(sessionprotocol.pointer_line("T", "move", (3.0, 4.0))))
    registry.handle_line(socket, parsed(sessionprotocol.pointer_line("T", "press", (5.0, 6.0))))

    assert log.moves == [("T", 3.0, 4.0)]
    assert log.presses == [("T", 5.0, 6.0)]


def test_ignores_pointer_lines_of_an_unregistered_connection() -> None:
    registry, _ = started_session()
    log = PointerLog()

    registry.handle_line(FakeSocket(), parsed(sessionprotocol.pointer_line("T", "move", (1, 2))))

    assert log.moves == []


@pytest.mark.parametrize(
    "line",
    [
        {"session": "pointer", "kind": "move", "x": 1, "y": 2},
        {"session": "pointer", "target": "T", "kind": "spin", "x": 1, "y": 2},
        {"session": "pointer", "target": "T", "kind": "move", "x": "1", "y": 2},
        {"session": "pointer", "target": "T", "kind": "move", "x": True, "y": 2},
    ],
)
def test_ignores_malformed_pointer_lines(line: dict[str, object]) -> None:
    registry, socket = started_session()
    log = PointerLog()

    registry.handle_line(socket, line)

    assert log.moves == []


def test_answers_which_tabs_are_open_to_agents() -> None:
    registry, socket = started_session()
    agent = TabAgent(False)
    AgentTabs.instance().watch(agent)
    agent.setTargetId("answered-tab")
    agent.allow()

    registry.handle_line(socket, {"session": "agent-tabs?"})

    listed = sessionprotocol.parse_agent_tabs(socket.written[-1])
    assert listed is not None and "answered-tab" in listed


def test_marks_the_tab_a_session_opened_with_its_name() -> None:
    registry, socket = started_session()
    agent = TabAgent(False)
    AgentTabs.instance().watch(agent)
    agent.setTargetId("opened-tab")

    registry.handle_line(socket, parsed(sessionprotocol.own_line("opened-tab")))

    assert (agent.hasAccess, agent.name) == (True, "Claude Code")


def test_pushes_access_changes_to_the_connected_sessions() -> None:
    _, socket = started_session()
    agent = TabAgent(False)
    AgentTabs.instance().watch(agent)
    agent.setTargetId("pushed-tab")

    agent.allow()
    agent.remove()

    changes = [sessionprotocol.parse_agent_tab_change(line) for line in socket.written[1:]]
    assert changes == [("pushed-tab", True), ("pushed-tab", False)]
