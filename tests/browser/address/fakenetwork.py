from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

UNKNOWN_SCHEME_URL = "foo://suggestions.example/"


def settle_replies() -> None:
    QCoreApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)


def data_url(body: str) -> QUrl:
    return QUrl("data:application/json," + QUrl.toPercentEncoding(body).data().decode())


class FakeNetworkAccessManager(QNetworkAccessManager):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[QNetworkRequest] = []
        self.answer = QUrl(UNKNOWN_SCHEME_URL)

    def answer_with(self, body: str) -> None:
        self.answer = data_url(body)

    def answer_with_failure(self) -> None:
        self.answer = QUrl(UNKNOWN_SCHEME_URL)

    def get(self, request: QNetworkRequest) -> QNetworkReply:
        self.requests.append(QNetworkRequest(request))
        return super().get(QNetworkRequest(self.answer))
