from typing import NamedTuple

from PySide6.QtCore import QObject, QUrl, QUrlQuery, Signal, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.browser.address.suggestionlist import suggestions_from_json
from kondor.core.settings.settings import Settings

USER_AGENT = "Kondor Browser"
GOOGLE = "google"
QUERY_PARAMETER = "q"


class Endpoint(NamedTuple):
    address: str
    parameter: str
    value: str


GOOGLE_ENDPOINT = Endpoint(
    "https://suggestqueries.google.com/complete/search", "client", "firefox"
)
DUCKDUCKGO_ENDPOINT = Endpoint("https://duckduckgo.com/ac/", "type", "list")


def endpoint_for(search_engine: str) -> Endpoint:
    return GOOGLE_ENDPOINT if search_engine == GOOGLE else DUCKDUCKGO_ENDPOINT


def endpoint_url(text: str) -> QUrl:
    endpoint = endpoint_for(str(Settings.instance().property("searchEngine")))
    query = QUrlQuery()
    query.addQueryItem(endpoint.parameter, endpoint.value)
    query.addQueryItem(QUERY_PARAMETER, text)
    url = QUrl(endpoint.address)
    url.setQuery(query)
    return url


def build_request(text: str) -> QNetworkRequest:
    request = QNetworkRequest(endpoint_url(text))
    request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, USER_AGENT)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    return request


def suggestions_of(reply: QNetworkReply) -> list[str]:
    if reply.error() != QNetworkReply.NetworkError.NoError:
        return []
    return suggestions_from_json(reply.readAll().data())


class SearchSuggestions(QObject):
    suggestionsReady = Signal(str, "QStringList")
    _instance: "SearchSuggestions | None" = None

    def __init__(self, manager: QNetworkAccessManager | None = None) -> None:
        super().__init__()
        self._manager = manager if manager is not None else QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._pending_text = ""

    @classmethod
    def instance(cls) -> "SearchSuggestions":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str)
    def request(self, text: str) -> None:
        query = text.strip()
        self.cancel()
        if not query:
            return
        self._pending_text = query
        self.send(build_request(query))

    @Slot()
    def cancel(self) -> None:
        reply = self._reply
        if reply is None:
            return
        self._reply = None
        reply.abort()
        reply.deleteLater()

    def send(self, request: QNetworkRequest) -> None:
        reply = self._manager.get(request)
        self._reply = reply
        reply.finished.connect(lambda: self.handle_reply(reply))

    def handle_reply(self, reply: QNetworkReply) -> None:
        if reply is not self._reply:
            return
        self._reply = None
        reply.deleteLater()
        self.suggestionsReady.emit(self._pending_text, suggestions_of(reply))
