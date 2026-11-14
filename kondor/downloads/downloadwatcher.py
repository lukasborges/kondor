import weakref

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from kondor.downloads.downloadroles import Role

TOTAL_ROLES = [Role.TotalBytesRole, Role.ProgressRole]
FILE_NAME_ROLES = [Role.FileNameRole]
INTERRUPT_REASON_ROLES = [Role.InterruptReasonStringRole]


class DownloadWatcher(QObject):
    receivedBytesChanged = Signal(object)
    stateChanged = Signal(object)
    pausedChanged = Signal(object)
    downloadDestroyed = Signal(object)
    rolesChanged = Signal(object, list)

    def __init__(self, download: QWebEngineDownloadRequest) -> None:
        super().__init__()
        self._download = weakref.ref(download)
        self.connect_progress_signals(download)
        self.connect_state_signals(download)
        download.destroyed.connect(self.on_destroyed)

    def connect_progress_signals(self, download: QWebEngineDownloadRequest) -> None:
        download.receivedBytesChanged.connect(self.on_received_bytes_changed)
        download.totalBytesChanged.connect(self.on_total_bytes_changed)
        download.downloadFileNameChanged.connect(self.on_file_name_changed)

    def connect_state_signals(self, download: QWebEngineDownloadRequest) -> None:
        download.stateChanged.connect(self.on_state_changed)
        download.isPausedChanged.connect(self.on_paused_changed)
        download.interruptReasonChanged.connect(self.on_interrupt_reason_changed)

    @Slot()
    def on_received_bytes_changed(self) -> None:
        self.receivedBytesChanged.emit(self._download())

    @Slot()
    def on_total_bytes_changed(self) -> None:
        self.rolesChanged.emit(self._download(), TOTAL_ROLES)

    @Slot()
    def on_file_name_changed(self) -> None:
        self.rolesChanged.emit(self._download(), FILE_NAME_ROLES)

    @Slot()
    def on_state_changed(self) -> None:
        self.stateChanged.emit(self._download())

    @Slot()
    def on_paused_changed(self) -> None:
        self.pausedChanged.emit(self._download())

    @Slot()
    def on_interrupt_reason_changed(self) -> None:
        self.rolesChanged.emit(self._download(), INTERRUPT_REASON_ROLES)

    @Slot()
    def on_destroyed(self) -> None:
        self.downloadDestroyed.emit(self._download())
