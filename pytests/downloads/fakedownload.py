from typing import cast

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

State = QWebEngineDownloadRequest.DownloadState


class FakeDownload(QObject):
    receivedBytesChanged = Signal()
    totalBytesChanged = Signal()
    downloadFileNameChanged = Signal()
    stateChanged = Signal(object)
    isPausedChanged = Signal()
    interruptReasonChanged = Signal()

    def __init__(self, file_name: str = "", is_save_page: bool = False) -> None:
        super().__init__()
        self._state = State.DownloadRequested
        self._is_paused = False
        self._received, self._total = 0, 0
        self._file_name, self._directory = file_name, ""
        self._is_save_page = is_save_page
        self._interrupt_reason = ""
        self.was_accepted = False

    def as_request(self) -> QWebEngineDownloadRequest:
        return cast(QWebEngineDownloadRequest, self)

    def state(self) -> QWebEngineDownloadRequest.DownloadState:
        return self._state

    def isPaused(self) -> bool:
        return self._is_paused

    def receivedBytes(self) -> int:
        return self._received

    def totalBytes(self) -> int:
        return self._total

    def mimeType(self) -> str:
        return ""

    def url(self) -> QUrl:
        return QUrl("https://example.org/file")

    def downloadFileName(self) -> str:
        return self._file_name

    def suggestedFileName(self) -> str:
        return "suggested.bin"

    def downloadDirectory(self) -> str:
        return self._directory

    def isSavePageDownload(self) -> bool:
        return self._is_save_page

    def interruptReasonString(self) -> str:
        return self._interrupt_reason

    def setDownloadFileName(self, name: str) -> None:
        self._file_name = name
        self.downloadFileNameChanged.emit()

    def setDownloadDirectory(self, directory: str) -> None:
        self._directory = directory

    def accept(self) -> None:
        self.was_accepted = True

    def pause(self) -> None:
        self.set_paused(True)

    def resume(self) -> None:
        self.set_paused(False)

    def cancel(self) -> None:
        self.set_state(State.DownloadCancelled)

    def set_state(self, state: QWebEngineDownloadRequest.DownloadState) -> None:
        self._state = state
        self.stateChanged.emit(state)

    def set_paused(self, is_paused: bool) -> None:
        self._is_paused = is_paused
        self.isPausedChanged.emit()

    def set_bytes(self, received: int, total: int) -> None:
        self._received, self._total = received, total
        self.totalBytesChanged.emit()
        self.receivedBytesChanged.emit()

    def set_interrupt_reason(self, reason: str) -> None:
        self._interrupt_reason = reason
        self.interruptReasonChanged.emit()
