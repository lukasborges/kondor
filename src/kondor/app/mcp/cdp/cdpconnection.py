import json
from typing import Any

from PySide6.QtCore import QObject, QUrl
from PySide6.QtWebSockets import QWebSocket

from kondor.app.mcp.cdp.blocking import wait_until
from kondor.app.mcp.cdp.pagesession import CdpParams
from kondor.app.mcp.protocol.toolresult import ToolFailureError

CONNECT_TIMEOUT_MILLISECONDS = 5000
COMMAND_TIMEOUT_MILLISECONDS = 30000


def origin_of(url: str) -> str:
    parsed = QUrl(url)
    return f"http://{parsed.host()}:{parsed.port()}"


class CdpConnection(QObject):
    def __init__(self, url: str) -> None:
        super().__init__()
        self._socket = QWebSocket(origin=origin_of(url))
        self._url = url
        self._next_id = 0
        self._replies: dict[int, dict[str, Any]] = {}
        self._events: list[str] = []
        self._socket.textMessageReceived.connect(self.receive)
        self.isolated_worlds: dict[str, int] = {}

    def open(self) -> bool:
        self._socket.open(QUrl(self._url))
        return wait_until(self.is_open, CONNECT_TIMEOUT_MILLISECONDS)

    def is_open(self) -> bool:
        return bool(self._socket.isValid())

    def local_port(self) -> int:
        return int(self._socket.localPort())

    def close(self) -> None:
        self._socket.close()

    def call(self, method: str, params: CdpParams | None = None) -> CdpParams:
        self._next_id += 1
        command_id = self._next_id
        self._socket.sendTextMessage(
            json.dumps({"id": command_id, "method": method, "params": params or {}})
        )
        if not wait_until(lambda: self.has_reply(command_id), COMMAND_TIMEOUT_MILLISECONDS):
            raise ToolFailureError(f"The page did not answer {method} in time.")
        return self.result_of(self._replies.pop(command_id, None), method)

    def has_reply(self, command_id: int) -> bool:
        return command_id in self._replies or not self.is_open()

    @staticmethod
    def result_of(reply: dict[str, Any] | None, method: str) -> CdpParams:
        if reply is None:
            raise ToolFailureError("The page connection closed.")
        if "error" in reply:
            raise ToolFailureError(
                f"{method} failed: {reply['error'].get('message', 'unknown error')}"
            )
        return dict(reply.get("result", {}))

    def receive(self, text: str) -> None:
        message = json.loads(text)
        if "id" in message:
            self._replies[message["id"]] = message
        elif "method" in message:
            self._events.append(message["method"])

    def clear_events(self) -> None:
        self._events.clear()

    def wait_for_event(self, name: str, timeout_milliseconds: int) -> bool:
        return wait_until(lambda: name in self._events, timeout_milliseconds)
