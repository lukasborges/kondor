from PySide6.QtCore import QObject, QUrl
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket

DEFAULT_PAGE = b"<html><head><title>t</title></head><body>page</body></html>"
NOT_FOUND = b"not found"


def http_response(status: str, body: bytes) -> bytes:
    head = f"HTTP/1.1 {status}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    return head.encode() + body


def requested_path(request: bytes) -> str:
    parts = request.split(b" ", 2)
    return parts[1].decode() if len(parts) > 1 else "/"


class PageServer(QObject):
    def __init__(self, bodies: dict[str, bytes] | None = None) -> None:
        super().__init__()
        self.bodies = bodies if bodies is not None else {"/": DEFAULT_PAGE}
        self.requests: list[str] = []
        self.server = QTcpServer(self)
        self.server.listen(QHostAddress.SpecialAddress.LocalHost, 0)
        self.server.newConnection.connect(self.accept_connections)

    def port(self) -> int:
        return int(self.server.serverPort())

    def url(self, path: str = "/") -> QUrl:
        return QUrl(f"http://127.0.0.1:{self.port()}{path}")

    def accept_connections(self) -> None:
        while (socket := self.server.nextPendingConnection()) is not None:
            socket.readyRead.connect(lambda socket=socket: self.respond(socket))
            socket.disconnected.connect(socket.deleteLater)

    def respond(self, socket: QTcpSocket) -> None:
        path = requested_path(bytes(socket.readAll().data()))
        self.requests.append(path)
        body = self.bodies.get(path)
        socket.write(http_response("200 OK", body) if body is not None else self.missing())
        socket.disconnectFromHost()

    @staticmethod
    def missing() -> bytes:
        return http_response("404 Not Found", NOT_FOUND)
