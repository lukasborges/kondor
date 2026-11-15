import os
from enum import Enum
from typing import cast

from PySide6.QtCore import (
    QByteArray,
    QCryptographicHash,
    QDir,
    QObject,
    QStandardPaths,
    Signal,
    qWarning,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from kondor.app.instance.singleinstancemessage import (
    SingleInstanceMessage,
    from_json_line,
    to_json_line,
)

MAX_MESSAGE_SIZE = 1024 * 1024
SOCKET_TIMEOUT_MILLISECONDS = 500


class StartResult(Enum):
    LISTENING = "listening"
    FORWARDED = "forwarded"
    FAILED = "failed"


def profile_hash() -> str:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    digest = QCryptographicHash.hash(
        QByteArray(location.encode("utf-8")), QCryptographicHash.Algorithm.Sha1
    )
    return bytes(digest.toHex()).decode("ascii")[:16]


def runtime_directory() -> str:
    location = QStandardPaths.StandardLocation.RuntimeLocation
    directory = str(QStandardPaths.writableLocation(location))
    flatpak_id = os.environ.get("FLATPAK_ID", "")
    if not flatpak_id:
        return directory
    shared = f"{directory}/app/{flatpak_id}"
    QDir().mkpath(shared)
    return shared


def wait_until_disconnected(socket: QLocalSocket) -> None:
    socket.disconnectFromServer()
    if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
        socket.waitForDisconnected(SOCKET_TIMEOUT_MILLISECONDS)


def has_unsent_bytes(socket: QLocalSocket) -> bool:
    return bool(socket.bytesToWrite() > 0)


class SingleInstance(QObject):
    messageReceived = Signal(object)

    def __init__(self, server_name: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name = server_name or SingleInstance.server_name()
        self._server = QLocalServer(self)
        self._buffers: dict[QLocalSocket, bytes] = {}
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self._server.newConnection.connect(self.handle_new_connection)

    @staticmethod
    def server_name() -> str:
        return f"{runtime_directory()}/kondor-{profile_hash()}.socket"

    def send_message(self, message: SingleInstanceMessage) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._name)
        if not socket.waitForConnected(SOCKET_TIMEOUT_MILLISECONDS):
            return False
        socket.write(QByteArray(to_json_line(message)))
        if has_unsent_bytes(socket) and not socket.waitForBytesWritten(SOCKET_TIMEOUT_MILLISECONDS):
            return False
        wait_until_disconnected(socket)
        return True

    def start(self, message: SingleInstanceMessage) -> StartResult:
        if self.send_message(message):
            return StartResult.FORWARDED
        QLocalServer.removeServer(self._name)
        if self._server.listen(self._name):
            return StartResult.LISTENING
        return StartResult.FORWARDED if self.send_message(message) else StartResult.FAILED

    def handle_new_connection(self) -> None:
        while (socket := self._server.nextPendingConnection()) is not None:
            self.watch(socket)

    def watch(self, socket: QLocalSocket) -> None:
        self._buffers[socket] = b""
        socket.readyRead.connect(self.read_from_sender)
        socket.disconnected.connect(self.forget_sender)
        self.read_from(socket)

    def read_from_sender(self) -> None:
        self.read_from(cast(QLocalSocket, self.sender()))

    def forget_sender(self) -> None:
        socket = cast(QLocalSocket, self.sender())
        self._buffers.pop(socket, None)
        socket.deleteLater()

    def read_from(self, socket: QLocalSocket) -> None:
        if socket not in self._buffers:
            return
        if self.buffer_incoming(socket):
            self.emit_complete_lines(socket)

    def buffer_incoming(self, socket: QLocalSocket) -> bool:
        self._buffers[socket] += bytes(socket.readAll())
        if len(self._buffers[socket]) <= MAX_MESSAGE_SIZE:
            return True
        qWarning("Kondor: single-instance message too large, ignored")
        self._buffers[socket] = b""
        socket.disconnectFromServer()
        return False

    def emit_complete_lines(self, socket: QLocalSocket) -> None:
        *lines, rest = self._buffers[socket].split(b"\n")
        self._buffers[socket] = rest
        for line in lines:
            self.messageReceived.emit(from_json_line(line))
