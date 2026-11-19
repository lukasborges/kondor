from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QFile, QIODevice, QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.translate.storage.filehash import matches_hash

STALL_TIMEOUT_MILLISECONDS = 60_000


class FileTask(NamedTuple):
    url: str
    destination: Path
    hash: str
    size: int


class FileDownloader(QObject):
    progressed = Signal(int)
    finished = Signal(bool)

    def __init__(self, manager: QNetworkAccessManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._reply: QNetworkReply | None = None
        self._file: QFile | None = None
        self._task: FileTask | None = None

    def start(self, task: FileTask) -> None:
        self._task = task
        task.destination.parent.mkdir(parents=True, exist_ok=True)
        self._file = QFile(str(task.destination))
        if not self._file.open(QIODevice.OpenModeFlag.WriteOnly):
            self.finished.emit(False)
            return
        self._request(task.url)

    def cancel(self) -> None:
        if self._reply is not None:
            self._reply.abort()

    def _request(self, url: str) -> None:
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(STALL_TIMEOUT_MILLISECONDS)
        self._reply = self._manager.get(request)
        self._reply.readyRead.connect(self._write_available)
        self._reply.downloadProgress.connect(
            lambda received, _total: self.progressed.emit(received)
        )
        self._reply.finished.connect(self._on_finished)

    def _write_available(self) -> None:
        if self._reply is not None and self._file is not None:
            self._file.write(self._reply.readAll())

    def _on_finished(self) -> None:
        reply, file, task = self._reply, self._file, self._task
        if reply is None or file is None or task is None:
            return
        self._write_available()
        file.close()
        ok = reply.error() == QNetworkReply.NetworkError.NoError
        reply.deleteLater()
        self._reply = None
        self.finished.emit(ok and matches_hash(task.destination, task.hash))
