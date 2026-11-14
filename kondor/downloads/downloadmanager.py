from enum import IntEnum

from PySide6.QtCore import (
    Property,
    QAbstractItemModel,
    QCoreApplication,
    QEnum,
    QObject,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWebEngineQuick import QQuickWebEngineDownloadRequest

from kondor.core.notifier import Notifier
from kondor.core.settings.settings import Settings
from kondor.downloads import downloadactions, downloadroles
from kondor.downloads.downloadmodel import DownloadModel

DownloadState = QWebEngineDownloadRequest.DownloadState
NOTIFICATION_ICON = "download"


def notify(title: str, body: str) -> None:
    Notifier.instance().notify(title, body, NOTIFICATION_ICON)


def notify_completed(download: QWebEngineDownloadRequest) -> None:
    title = QCoreApplication.translate("DownloadManager", "Download completed")
    notify(title, download.downloadFileName())


def notify_failed(download: QWebEngineDownloadRequest) -> None:
    title = QCoreApplication.translate("DownloadManager", "Download failed")
    notify(title, download.interruptReasonString() or download.downloadFileName())


def notify_state(download: QWebEngineDownloadRequest, state: object) -> None:
    if state == DownloadState.DownloadCompleted:
        notify_completed(download)
    elif state == DownloadState.DownloadInterrupted:
        notify_failed(download)


def asks_where_to_save(download: QWebEngineDownloadRequest) -> bool:
    is_asking = bool(Settings.instance().property("askWhereToSave"))
    return is_asking and not download.isSavePageDownload()


class DownloadManager(QObject):
    @QEnum
    class State(IntEnum):
        Requested = DownloadState.DownloadRequested.value
        InProgress = DownloadState.DownloadInProgress.value
        Completed = DownloadState.DownloadCompleted.value
        Cancelled = DownloadState.DownloadCancelled.value
        Interrupted = DownloadState.DownloadInterrupted.value

    saveLocationRequested = Signal(QQuickWebEngineDownloadRequest, QUrl)
    downloadStarted = Signal()
    activeChanged = Signal()
    _instance: "DownloadManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._model = DownloadModel(self)
        QCoreApplication.instance().aboutToQuit.connect(self._model.remove_private_downloads)
        self._model.activeChanged.connect(self.activeChanged)

    @classmethod
    def instance(cls) -> "DownloadManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def download_model(self) -> DownloadModel:
        return self._model

    def has_active_downloads(self) -> bool:
        return self._model.has_active_downloads()

    def active_progress(self) -> float:
        return self._model.active_progress()

    def has_finished_downloads(self) -> bool:
        return self._model.has_finished_downloads()

    model = Property(QAbstractItemModel, download_model, constant=True)
    hasActiveDownloads = Property(bool, has_active_downloads, notify=activeChanged)
    activeProgress = Property(float, active_progress, notify=activeChanged)
    hasFinishedDownloads = Property(bool, has_finished_downloads, notify=activeChanged)

    def handle_request(
        self, download: QWebEngineDownloadRequest | None, is_private: bool = False
    ) -> None:
        if download is None:
            return
        downloadactions.choose_target(download)
        self._model.add_download(download, is_private)
        download.stateChanged.connect(lambda state: notify_state(download, state))
        self.accept_or_ask(download)
        self.downloadStarted.emit()

    def accept_or_ask(self, download: QWebEngineDownloadRequest) -> None:
        if asks_where_to_save(download):
            self.request_save_location(download)
        else:
            download.accept()

    def request_save_location(self, download: QWebEngineDownloadRequest) -> None:
        if not isinstance(download, QQuickWebEngineDownloadRequest):
            download.accept()
            return
        target = QUrl.fromLocalFile(downloadactions.target_path_of(download))
        self.saveLocationRequested.emit(download, target)

    @Slot(int)
    def pause(self, row: int) -> None:
        download = self._model.download_at(row)
        if download is not None and downloadactions.can_pause(download):
            download.pause()

    @Slot(int)
    def resume(self, row: int) -> None:
        download = self._model.download_at(row)
        if download is not None and downloadactions.can_resume(download):
            download.resume()

    @Slot(int)
    def cancel(self, row: int) -> None:
        download = self._model.download_at(row)
        if download is not None and downloadroles.is_active_download(download):
            download.cancel()

    @Slot(int)
    def openFile(self, row: int) -> None:
        downloadactions.open_file(self._model.download_at(row))

    @Slot(int)
    def showInFolder(self, row: int) -> None:
        downloadactions.show_in_folder(self._model.download_at(row))

    @Slot(int)
    def removeFromList(self, row: int) -> None:
        self._model.remove_download(row)

    @Slot()
    def clearFinished(self) -> None:
        self._model.clear_finished()

    @Slot()
    def openDownloadsFolder(self) -> None:
        downloadactions.open_local_path(Settings.instance().property("downloadDirectory"))
