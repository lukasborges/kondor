import pytest
from PySide6.QtCore import QObject, Signal

from kondor.app.instance.sessionprotocol import RemoteControlState
from kondor.app.remotecontrol.connections.automationpoller import AutomationPoller
from kondor.app.remotecontrol.connections.connection import Connection
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.app.remotecontrol.connections.sessionregistry import SessionRegistry

pytestmark = pytest.mark.usefixtures("qapp")
PORT = 9222
TABLE = (
    "header\n   0: 0100007F:2406 0100007F:C350 01 00000000:00000000 00:00000000 00000000 1000 0 1\n"
)


class FakeSocket(QObject):
    disconnected = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(bytes(data))

    def disconnectFromServer(self) -> None:  # noqa: N802
        return None


def hello(name: str) -> dict[str, object]:
    return {"session": "hello", "clientName": name, "clientVersion": "1"}


def test_starts_empty() -> None:
    model = ConnectionModel()

    assert model.rowCount() == 0
    assert model.property("count") == 0
    assert model.property("firstName") == ""


def test_registers_a_session_and_names_it() -> None:
    model = ConnectionModel()
    registry = SessionRegistry(model)
    registry.state = RemoteControlState(True, PORT)

    registry.handle_line(FakeSocket(), hello("Claude Code"))

    assert model.property("count") == 1
    assert model.property("firstName") == "Claude Code"


def test_replies_with_the_remote_control_state() -> None:
    registry = SessionRegistry(ConnectionModel())
    registry.state = RemoteControlState(True, PORT)
    socket = FakeSocket()

    registry.handle_line(socket, hello("x"))

    assert socket.written == [b'{"active":true,"port":9222}\n']


def test_does_not_register_a_session_while_remote_control_is_off() -> None:
    model = ConnectionModel()
    registry = SessionRegistry(model)
    socket = FakeSocket()

    registry.handle_line(socket, hello("x"))

    assert model.rowCount() == 0
    assert socket.written == [b'{"active":false,"port":0}\n']


def test_removes_the_session_when_its_socket_closes() -> None:
    model = ConnectionModel()
    registry = SessionRegistry(model)
    registry.state = RemoteControlState(True, PORT)
    registry.handle_line(FakeSocket(), hello("x"))

    registry.end_session(next(iter(registry._sessions)))

    assert model.rowCount() == 0


def test_tracks_the_ports_a_session_announces() -> None:
    model = ConnectionModel()
    registry = SessionRegistry(model)
    registry.state = RemoteControlState(True, PORT)
    socket = FakeSocket()
    registry.handle_line(socket, hello("x"))

    registry.handle_line(socket, {"session": "ports", "ports": [50000]})

    assert model.session_ports() == {50000}


def test_shows_an_automation_tool_after_two_polls_and_hides_it_after_it_leaves() -> None:
    model = ConnectionModel()
    table = {"text": TABLE}
    poller = AutomationPoller(model, PORT, lambda: table["text"])

    poller.poll()
    assert model.rowCount() == 0
    poller.poll()
    assert model.rowCount() == 1
    assert model.property("firstName") == ""
    table["text"] = ""
    poller.poll()
    assert model.rowCount() == 0


def test_ignores_the_ports_of_mcp_sessions() -> None:
    model = ConnectionModel()
    model.add(Connection("Claude Code", socket=FakeSocket(), ports=[0xC350]))
    poller = AutomationPoller(model, PORT, lambda: TABLE)

    poller.poll()
    poller.poll()

    assert model.find_automation() is None
