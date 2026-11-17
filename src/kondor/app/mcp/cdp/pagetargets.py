import json
from dataclasses import dataclass

from PySide6.QtCore import QObject, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.app.mcp.cdp.blocking import wait_until
from kondor.app.mcp.protocol.toolresult import ToolFailureError

LIST_TIMEOUT_MILLISECONDS = 5000


@dataclass(frozen=True)
class PageTarget:
    id: str
    title: str
    url: str
    socket_url: str


def parse_targets(body: bytes) -> list[PageTarget]:
    try:
        entries = json.loads(body)
    except ValueError:
        return []
    return [target_of(entry) for entry in entries if is_page(entry)]


def is_page(entry: dict[str, str]) -> bool:
    return entry.get("type") == "page" and "webSocketDebuggerUrl" in entry


def target_of(entry: dict[str, str]) -> PageTarget:
    return PageTarget(
        id=entry["id"],
        title=entry.get("title", ""),
        url=entry.get("url", ""),
        socket_url=entry["webSocketDebuggerUrl"],
    )


class TargetLister(QObject):
    def __init__(self, port: int) -> None:
        super().__init__()
        self._address = f"http://127.0.0.1:{port}/json/list"
        self._manager = QNetworkAccessManager(self)

    def list_pages(self) -> list[PageTarget]:
        request = QNetworkRequest(QUrl(self._address))
        request.setRawHeader(b"Connection", b"close")
        reply = self._manager.get(request)
        finished = wait_until(reply.isFinished, LIST_TIMEOUT_MILLISECONDS)
        body = bytes(reply.readAll())
        failed = not finished or reply.error() != QNetworkReply.NetworkError.NoError
        reply.deleteLater()
        if failed:
            raise ToolFailureError("Kondor's remote control does not answer.")
        return parse_targets(body)
