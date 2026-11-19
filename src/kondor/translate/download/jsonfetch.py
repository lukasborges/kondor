import json
from collections.abc import Callable

from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

TIMEOUT_MILLISECONDS = 30_000
JsonCallback = Callable[[object | None], None]


def parse_json(data: bytes) -> object | None:
    try:
        result: object = json.loads(data.decode("utf-8"))
        return result
    except ValueError:
        return None


def reply_to_json(reply: QNetworkReply) -> object | None:
    ok = reply.error() == QNetworkReply.NetworkError.NoError
    return parse_json(bytes(reply.readAll().data())) if ok else None


def make_request(url: str) -> QNetworkRequest:
    request = QNetworkRequest(QUrl(url))
    request.setTransferTimeout(TIMEOUT_MILLISECONDS)
    return request


def fetch_json(manager: QNetworkAccessManager, url: str, callback: JsonCallback) -> QNetworkReply:
    reply = manager.get(make_request(url))
    reply.finished.connect(lambda: finish(reply, callback))
    return reply


def finish(reply: QNetworkReply, callback: JsonCallback) -> None:
    result = reply_to_json(reply)
    reply.deleteLater()
    callback(result)
