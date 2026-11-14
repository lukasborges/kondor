from PySide6.QtCore import QDir, QUrl
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from kondor.core.settings.settings import Settings

State = QWebEngineDownloadRequest.DownloadState
FILE_MANAGER_SERVICE = "org.freedesktop.FileManager1"
FILE_MANAGER_PATH = "/org/freedesktop/FileManager1"
SHOW_ITEMS_METHOD = "ShowItems"


def target_path_of(download: QWebEngineDownloadRequest) -> str:
    return str(QDir(download.downloadDirectory()).filePath(download.downloadFileName()))


def choose_target(download: QWebEngineDownloadRequest) -> None:
    if download.isSavePageDownload():
        return
    download.setDownloadDirectory(Settings.instance().property("downloadDirectory"))
    if not download.downloadFileName():
        download.setDownloadFileName(download.suggestedFileName())


def file_manager_interface() -> QDBusInterface:
    return QDBusInterface(
        FILE_MANAGER_SERVICE, FILE_MANAGER_PATH, FILE_MANAGER_SERVICE, QDBusConnection.sessionBus()
    )


def show_in_file_manager(path: str) -> bool:
    file_manager = file_manager_interface()
    if not file_manager.isValid():
        return False
    items = [QUrl.fromLocalFile(path).toString()]
    reply = file_manager.call(SHOW_ITEMS_METHOD, items, "")
    return bool(reply.type() != QDBusMessage.MessageType.ErrorMessage)


def open_local_path(path: str) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def is_running(download: QWebEngineDownloadRequest) -> bool:
    return bool(download.state() == State.DownloadInProgress)


def can_pause(download: QWebEngineDownloadRequest) -> bool:
    return is_running(download) and not bool(download.isPaused())


def can_resume(download: QWebEngineDownloadRequest) -> bool:
    return is_running(download) and bool(download.isPaused())


def open_file(download: QWebEngineDownloadRequest | None) -> None:
    if download is None or download.state() != State.DownloadCompleted:
        return
    open_local_path(target_path_of(download))


def show_in_folder(download: QWebEngineDownloadRequest | None) -> None:
    if download is None or show_in_file_manager(target_path_of(download)):
        return
    open_local_path(download.downloadDirectory())
