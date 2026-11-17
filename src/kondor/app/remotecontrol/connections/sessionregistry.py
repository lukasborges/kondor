from typing import Any

from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QLocalSocket

from kondor.app.instance import sessionprotocol
from kondor.app.instance.sessionprotocol import RemoteControlState
from kondor.app.remotecontrol.connections.connection import Connection
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel


class SessionRegistry:
    def __init__(self, model: ConnectionModel) -> None:
        self._model = model
        self._sessions: dict[QLocalSocket, Connection] = {}
        self.state = RemoteControlState(False, 0)

    def handle_line(self, socket: QLocalSocket, parsed: dict[str, Any]) -> None:
        if parsed.get("session") == "hello":
            self.start_session(socket, parsed)
        elif parsed.get("session") == "ports" and socket in self._sessions:
            self._sessions[socket].ports = sessionprotocol.parse_ports(parsed)

    def start_session(self, socket: QLocalSocket, parsed: dict[str, Any]) -> None:
        socket.write(QByteArray(sessionprotocol.reply_line(self.state)))
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
