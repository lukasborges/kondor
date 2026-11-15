from PySide6.QtCore import QByteArray, QDir, QFileInfo, QIODevice, QObject, QSaveFile, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.adblock.lists.filterlists import (
    FilterListSource,
    filter_cache_directory,
    filter_cache_path,
    filter_list_sources,
)

TIMEOUT_MILLISECONDS = 60000
MINIMUM_LIST_BYTES = 1024
HTTP_OK = 200
HTTP_NOT_MODIFIED = 304


def set_if_modified_since(request: QNetworkRequest, source: FilterListSource) -> None:
    cached = QFileInfo(filter_cache_path(source))
    if cached.exists():
        modified = cached.lastModified().toUTC()
        request.setHeader(QNetworkRequest.KnownHeaders.IfModifiedSinceHeader, modified)


def request_for(source: FilterListSource) -> QNetworkRequest:
    request = QNetworkRequest(QUrl(source.url))
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    request.setTransferTimeout(TIMEOUT_MILLISECONDS)
    set_if_modified_since(request, source)
    return request


def save_list(path: str, body: QByteArray) -> bool:
    file = QSaveFile(path)
    if body.size() <= MINIMUM_LIST_BYTES or not file.open(QIODevice.OpenModeFlag.WriteOnly):
        return False
    file.write(body)
    return bool(file.commit())


def http_status(reply: QNetworkReply) -> int:
    status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
    return int(status or 0)


def is_reply_usable(reply: QNetworkReply, status: int) -> bool:
    return reply.error() == QNetworkReply.NetworkError.NoError and status == HTTP_OK


class FilterListDownloader(QObject):
    updatingChanged = Signal()
    finished = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._network: QNetworkAccessManager | None = None
        self._pending_downloads = 0
        self._is_any_list_current = False

    def is_updating(self) -> bool:
        return self._pending_downloads > 0

    def update(self) -> None:
        if self.is_updating():
            return
        QDir().mkpath(filter_cache_directory())
        self._is_any_list_current = False
        self._pending_downloads = len(filter_list_sources())
        self.updatingChanged.emit()
        for source in filter_list_sources():
            self._download(source)

    def _network_manager(self) -> QNetworkAccessManager:
        if self._network is None:
            self._network = QNetworkAccessManager(self)
        return self._network

    def _download(self, source: FilterListSource) -> None:
        reply = self._network_manager().get(request_for(source))
        path = filter_cache_path(source)
        reply.finished.connect(lambda: self._handle_reply(reply, path))

    def _handle_reply(self, reply: QNetworkReply, path: str) -> None:
        reply.deleteLater()
        status = http_status(reply)
        is_saved = is_reply_usable(reply, status) and save_list(path, reply.readAll())
        if is_saved or status == HTTP_NOT_MODIFIED:
            self._is_any_list_current = True
        self._finish_one_list()

    def _finish_one_list(self) -> None:
        self._pending_downloads -= 1
        if self._pending_downloads > 0:
            return
        self.finished.emit(self._is_any_list_current)
        self.updatingChanged.emit()
