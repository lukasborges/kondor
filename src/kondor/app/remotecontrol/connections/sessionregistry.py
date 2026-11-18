from typing import Any

from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QLocalSocket

from kondor.app.instance import sessionprotocol
from kondor.app.instance.sessionprotocol import RemoteControlState
from kondor.app.remotecontrol.connections.connection import Connection
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.browser.agent.agentpointer import AgentPointer
from kondor.browser.agent.agenttabs import AgentTabs


class SessionRegistry:
    def __init__(self, model: ConnectionModel) -> None:
        self._model = model
        self._sessions: dict[QLocalSocket, Connection] = {}
        self.state = RemoteControlState(False, 0)
        AgentTabs.instance().tabAccessChanged.connect(self.push_access_change)

    def handle_line(self, socket: QLocalSocket, parsed: dict[str, Any]) -> None:
        kind = parsed.get("session")
        if kind == "hello":
            self.start_session(socket, parsed)
        elif socket in self._sessions:
            self.handle_session_line(socket, kind, parsed)

    def handle_session_line(
        self, socket: QLocalSocket, kind: object, parsed: dict[str, Any]
    ) -> None:
        connection = self._sessions[socket]
        if kind == "ports":
            connection.ports = sessionprotocol.parse_ports(parsed)
        elif kind == "pointer":
            self.show_pointer(connection, parsed)
        elif kind == "own":
            AgentTabs.instance().own(sessionprotocol.parse_target(parsed), connection.name)
        elif kind == "agent-tabs?":
            self.write(socket, sessionprotocol.agent_tabs_line(AgentTabs.instance().target_ids()))

    def show_pointer(self, connection: Connection, parsed: dict[str, Any]) -> None:
        action = sessionprotocol.parse_pointer(parsed)
        if action is None:
            return
        AgentTabs.instance().note_activity(action.target_id, connection.name)
        AgentPointer.instance().announce(action)

    def push_access_change(self, target_id: str, has_access: bool) -> None:
        line = sessionprotocol.agent_tab_change_line(target_id, has_access)
        for socket in self._sessions:
            self.write(socket, line)

    def write(self, socket: QLocalSocket, line: bytes) -> None:
        socket.write(QByteArray(line))

    def start_session(self, socket: QLocalSocket, parsed: dict[str, Any]) -> None:
        self.write(socket, sessionprotocol.reply_line(self.state))
        if not self.state.is_active:
            return
        client = sessionprotocol.parse_client(parsed)
        connection = Connection(client.name or "AI agent", socket=socket)
        self._sessions[socket] = connection
        self._model.add(connection)
        socket.disconnected.connect(lambda: self.end_session(socket))

    def end_session(self, socket: QLocalSocket) -> None:
        connection = self._sessions.pop(socket, None)
        if connection is not None:
            self._model.remove(connection)
