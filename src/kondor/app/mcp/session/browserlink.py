from collections.abc import Callable

from PySide6.QtCore import QByteArray, QObject, Signal
from PySide6.QtNetwork import QLocalSocket

from kondor.app.instance import sessionprotocol
from kondor.app.instance.sessionprotocol import ClientIdentity, RemoteControlState
from kondor.app.mcp.cdp.blocking import wait_until

CONNECT_TIMEOUT_MILLISECONDS = 500
REPLY_TIMEOUT_MILLISECONDS = 5000
START_TIMEOUT_MILLISECONDS = 20000
RETRY_MILLISECONDS = 250


class BrowserLink(QObject):
    closed = Signal()

    def __init__(self, server_name: str, start_browser: Callable[[], None]) -> None:
        super().__init__()
        self._server_name = server_name
        self._start_browser = start_browser
        self._socket = QLocalSocket(self)
        self._init_incoming_state()
        self._socket.readyRead.connect(self.buffer_incoming)
        self._socket.disconnected.connect(self.handle_disconnect)

    def _init_incoming_state(self) -> None:
        self._buffer = b""
        self._has_reply = False
        self._state: RemoteControlState | None = None
        self._agent_tabs: set[str] | None = None
        self._is_closed = False

    def is_closed(self) -> bool:
        return self._is_closed

    def is_connected(self) -> bool:
        return bool(self._socket.state() == QLocalSocket.LocalSocketState.ConnectedState)

    def open_session(self, client: ClientIdentity) -> RemoteControlState | None:
        if not self.connect_or_start():
            return None
        self.write(sessionprotocol.hello_line(client))
        wait_until(lambda: self._has_reply or self._is_closed, REPLY_TIMEOUT_MILLISECONDS)
        if self._state is not None and self._state.is_active:
            self.fetch_agent_tabs()
        return self._state

    def fetch_agent_tabs(self) -> None:
        self.write(sessionprotocol.agent_tabs_query_line())
        wait_until(
            lambda: self._agent_tabs is not None or self._is_closed, REPLY_TIMEOUT_MILLISECONDS
        )

    def agent_tab_ids(self) -> set[str]:
        return set(self._agent_tabs or ())

    def add_agent_tab(self, target_id: str) -> None:
        self._agent_tabs = self.agent_tab_ids() | {target_id}
        self.write(sessionprotocol.own_line(target_id))

    def announce_pointer(self, target_id: str, kind: str, point: tuple[float, float]) -> None:
        self.write(sessionprotocol.pointer_line(target_id, kind, point))

    def write(self, line: bytes) -> None:
        if self.is_connected():
            self._socket.write(QByteArray(line))

    def connect_or_start(self) -> bool:
        if self.try_connect():
            return True
        self._start_browser()
        return (
            wait_until(self.try_connect_slowly, START_TIMEOUT_MILLISECONDS) and self.is_connected()
        )

    def try_connect_slowly(self) -> bool:
        if self.try_connect():
            return True
        wait_until(lambda: False, RETRY_MILLISECONDS)
        return False

    def try_connect(self) -> bool:
        self._socket.connectToServer(self._server_name)
        return bool(self._socket.waitForConnected(CONNECT_TIMEOUT_MILLISECONDS))

    def announce_ports(self, ports: list[int]) -> None:
        self.write(sessionprotocol.ports_line(ports))

    def buffer_incoming(self) -> None:
        self._buffer += bytes(self._socket.readAll())
        *lines, self._buffer = self._buffer.split(b"\n")
        for line in lines:
            self.receive(line)

    def receive(self, line: bytes) -> None:
        if not self._has_reply:
            self._state = sessionprotocol.parse_reply(line)
            self._has_reply = True
        else:
            self.apply_agent_tab_line(line)

    def apply_agent_tab_line(self, line: bytes) -> None:
        listed = sessionprotocol.parse_agent_tabs(line)
        if listed is not None:
            self._agent_tabs = set(listed)
        change = sessionprotocol.parse_agent_tab_change(line)
        if change is not None:
            self.apply_access_change(*change)

    def apply_access_change(self, target_id: str, has_access: bool) -> None:
        tabs = self.agent_tab_ids()
        self._agent_tabs = tabs | {target_id} if has_access else tabs - {target_id}

    def handle_disconnect(self) -> None:
        self._is_closed = True
        self.closed.emit()

    def close(self) -> None:
        self._socket.disconnectFromServer()
