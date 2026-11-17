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
        self._buffer = b""
        self._is_closed = False
        self._socket.readyRead.connect(self.buffer_reply)
        self._socket.disconnected.connect(self.handle_disconnect)

    def is_closed(self) -> bool:
        return self._is_closed

    def is_connected(self) -> bool:
        return bool(self._socket.state() == QLocalSocket.LocalSocketState.ConnectedState)

    def open_session(self, client: ClientIdentity) -> RemoteControlState | None:
        if not self.connect_or_start():
            return None
        self._socket.write(QByteArray(sessionprotocol.hello_line(client)))
        wait_until(lambda: b"\n" in self._buffer or self._is_closed, REPLY_TIMEOUT_MILLISECONDS)
        return sessionprotocol.parse_reply(self._buffer.partition(b"\n")[0])

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
        if self.is_connected():
            self._socket.write(QByteArray(sessionprotocol.ports_line(ports)))

    def buffer_reply(self) -> None:
        self._buffer += bytes(self._socket.readAll())

    def handle_disconnect(self) -> None:
        self._is_closed = True
        self.closed.emit()

    def close(self) -> None:
        self._socket.disconnectFromServer()
