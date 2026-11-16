from collections.abc import Callable, Sequence

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Signal,
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from kondor.downloads import downloadroles
from kondor.downloads.downloaditem import DownloadItem
from kondor.downloads.downloadroles import Role
from kondor.downloads.downloadwatcher import DownloadWatcher

State = QWebEngineDownloadRequest.DownloadState
NOT_FOUND = -1
RECEIVED_ROLES = (
    Role.ReceivedBytesRole,
    Role.TotalBytesRole,
    Role.ProgressRole,
    Role.SpeedTextRole,
)
STATE_ROLES = (
    Role.StateRole,
    Role.ReceivedBytesRole,
    Role.IsPausedRole,
    Role.ProgressRole,
    Role.SpeedTextRole,
    Role.InterruptReasonStringRole,
)
PAUSED_ROLES = (Role.IsPausedRole, Role.SpeedTextRole)


class DownloadModel(QAbstractListModel):
    Role = Role
    countChanged = Signal()
    activeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._items: list[DownloadItem] = []

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._items)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Role.FileNameRole
    ) -> object:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        return downloadroles.download_role_value(self._items[index.row()], role)

    def roleNames(self) -> dict[int, QByteArray]:
        return downloadroles.download_role_names()

    def item_count(self) -> int:
        return len(self._items)

    count = Property(int, item_count, notify=countChanged)

    def has_active_downloads(self) -> bool:
        live = downloadroles.live_downloads_of(self._items)
        return any(downloadroles.is_active_download(download) for download in live)

    def has_finished_downloads(self) -> bool:
        live = downloadroles.live_downloads_of(self._items)
        return any(downloadroles.is_finished_download(download) for download in live)

    def active_progress(self) -> float:
        return downloadroles.average_active_progress(downloadroles.live_downloads_of(self._items))

    def add_download(self, download: QWebEngineDownloadRequest | None, is_private: bool) -> None:
        if download is None or self.index_of(download) >= 0:
            return
        self.append_item(download, is_private)
        self.countChanged.emit()
        self.activeChanged.emit()

    def remove_download(self, row: int) -> None:
        if not 0 <= row < len(self._items):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row).release_watcher()
        self.endRemoveRows()
        self.countChanged.emit()
        self.activeChanged.emit()

    def clear_finished(self) -> None:
        self.remove_rows_where(lambda item: downloadroles.is_finished_download(self.live(item)))

    def remove_private_downloads(self) -> None:
        self.remove_rows_where(lambda item: item.is_private)

    def download_at(self, row: int) -> QWebEngineDownloadRequest | None:
        if not 0 <= row < len(self._items):
            return None
        return self.live(self._items[row])

    @staticmethod
    def live(item: DownloadItem) -> QWebEngineDownloadRequest | None:
        return item.download if item.is_live() else None

    def remove_rows_where(self, is_removed: Callable[[DownloadItem], bool]) -> None:
        for row in reversed(range(len(self._items))):
            if is_removed(self._items[row]):
                self.remove_download(row)

    def index_of(self, download: QWebEngineDownloadRequest) -> int:
        for row, item in enumerate(self._items):
            if item.download is download:
                return row
        return NOT_FOUND

    def item_of(self, download: QWebEngineDownloadRequest) -> DownloadItem | None:
        row = self.index_of(download)
        return None if row < 0 else self._items[row]

    def notify_row_changed(
        self, download: QWebEngineDownloadRequest, roles: Sequence[int]
    ) -> None:
        row = self.index_of(download)
        if row < 0:
            return
        self.dataChanged.emit(self.index(row), self.index(row), list(roles))
        self.activeChanged.emit()

    def append_item(self, download: QWebEngineDownloadRequest, is_private: bool) -> None:
        item = DownloadItem(self.watcher_of(download), download, is_private)
        item.speed.restart(download.receivedBytes())
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()

    def watcher_of(self, download: QWebEngineDownloadRequest) -> DownloadWatcher:
        watcher = DownloadWatcher(download)
        watcher.receivedBytesChanged.connect(self.on_received_bytes_changed)
        watcher.stateChanged.connect(self.on_state_changed)
        watcher.pausedChanged.connect(self.on_paused_changed)
        watcher.downloadDestroyed.connect(self.on_download_destroyed)
        watcher.rolesChanged.connect(self.notify_row_changed)
        return watcher

    def on_received_bytes_changed(self, download: QWebEngineDownloadRequest) -> None:
        item = self.item_of(download)
        if item is None:
            return
        item.speed.update(download.receivedBytes())
        self.notify_row_changed(download, RECEIVED_ROLES)

    def on_state_changed(self, download: QWebEngineDownloadRequest) -> None:
        item = self.item_of(download)
        if item is None:
            return
        if download.state() != State.DownloadInProgress:
            item.speed.stop()
        elif not download.isPaused():
            item.speed.restart(download.receivedBytes())
        self.notify_row_changed(download, STATE_ROLES)

    def on_paused_changed(self, download: QWebEngineDownloadRequest) -> None:
        item = self.item_of(download)
        if item is None:
            return
        if download.isPaused():
            item.speed.stop()
        else:
            item.speed.restart(download.receivedBytes())
        self.notify_row_changed(download, PAUSED_ROLES)

    def on_download_destroyed(self, download: QWebEngineDownloadRequest) -> None:
        self.remove_download(self.index_of(download))
