import math
from collections.abc import Callable, Sequence
from enum import IntEnum

from PySide6.QtCore import QByteArray, QLocale, QMimeDatabase, Qt
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from kondor.downloads.downloaditem import DownloadItem

State = QWebEngineDownloadRequest.DownloadState
ACTIVE_STATES = (State.DownloadRequested, State.DownloadInProgress)
FINISHED_STATES = (State.DownloadCompleted, State.DownloadCancelled, State.DownloadInterrupted)
DEFAULT_MIME_TYPE = "application/octet-stream"
DEFAULT_MIME_ICON = "application-octet-stream"
UNKNOWN_PROGRESS = -1.0


class Role(IntEnum):
    FileNameRole = Qt.ItemDataRole.UserRole + 1
    DirectoryRole = Qt.ItemDataRole.UserRole + 2
    UrlRole = Qt.ItemDataRole.UserRole + 3
    ReceivedBytesRole = Qt.ItemDataRole.UserRole + 4
    TotalBytesRole = Qt.ItemDataRole.UserRole + 5
    ProgressRole = Qt.ItemDataRole.UserRole + 6
    StateRole = Qt.ItemDataRole.UserRole + 7
    IsPausedRole = Qt.ItemDataRole.UserRole + 8
    IsPrivateRole = Qt.ItemDataRole.UserRole + 9
    SpeedTextRole = Qt.ItemDataRole.UserRole + 10
    InterruptReasonStringRole = Qt.ItemDataRole.UserRole + 11
    MimeIconNameRole = Qt.ItemDataRole.UserRole + 12


def is_active_download(download: QWebEngineDownloadRequest | None) -> bool:
    return download is not None and download.state() in ACTIVE_STATES


def is_finished_download(download: QWebEngineDownloadRequest | None) -> bool:
    return download is not None and download.state() in FINISHED_STATES


def received_fraction_of(download: QWebEngineDownloadRequest) -> float:
    total = download.totalBytes()
    if total <= 0:
        return UNKNOWN_PROGRESS
    return float(download.receivedBytes()) / float(total)


def progress_of(item: DownloadItem) -> float:
    fraction = received_fraction_of(item.download)
    return UNKNOWN_PROGRESS if fraction < 0.0 else min(fraction, 1.0)


def is_transferring(item: DownloadItem) -> bool:
    download = item.download
    is_running = download.state() == State.DownloadInProgress and not download.isPaused()
    return is_running and item.speed.bytes_per_second() > 0.0


def rounded_half_away_from_zero(value: float) -> int:
    return int(math.copysign(math.floor(abs(value) + 0.5), value))


def speed_text_of(item: DownloadItem) -> str:
    if not is_transferring(item):
        return ""
    bytes_per_second = rounded_half_away_from_zero(item.speed.bytes_per_second())
    return f"{QLocale().formattedDataSize(bytes_per_second)}/s"


def mime_icon_name_of(item: DownloadItem) -> str:
    mime_name = item.download.mimeType() or DEFAULT_MIME_TYPE
    icon_name = QMimeDatabase().mimeTypeForName(mime_name).iconName()
    return icon_name or DEFAULT_MIME_ICON


RoleReader = Callable[[DownloadItem], object]

ROLE_READERS: dict[int, tuple[bytes, RoleReader]] = {
    Role.FileNameRole: (b"fileName", lambda item: item.download.downloadFileName()),
    Role.DirectoryRole: (b"directory", lambda item: item.download.downloadDirectory()),
    Role.UrlRole: (b"url", lambda item: item.download.url()),
    Role.ReceivedBytesRole: (b"receivedBytes", lambda item: item.download.receivedBytes()),
    Role.TotalBytesRole: (b"totalBytes", lambda item: item.download.totalBytes()),
    Role.ProgressRole: (b"progress", progress_of),
    Role.StateRole: (b"state", lambda item: int(item.download.state().value)),
    Role.IsPausedRole: (b"isPaused", lambda item: item.download.isPaused()),
    Role.IsPrivateRole: (b"isPrivate", lambda item: item.is_private),
    Role.SpeedTextRole: (b"speedText", speed_text_of),
    Role.InterruptReasonStringRole: (
        b"interruptReasonString",
        lambda item: item.download.interruptReasonString(),
    ),
    Role.MimeIconNameRole: (b"mimeIconName", mime_icon_name_of),
}


def download_role_value(item: DownloadItem, role: int) -> object:
    entry = ROLE_READERS.get(role)
    if entry is None or not item.is_live():
        return None
    return entry[1](item)


def download_role_names() -> dict[int, QByteArray]:
    return {role: QByteArray(name) for role, (name, _) in ROLE_READERS.items()}


def average_active_progress(downloads: Sequence[QWebEngineDownloadRequest]) -> float:
    fractions = [
        received_fraction_of(download)
        for download in downloads
        if is_active_download(download) and download.totalBytes() > 0
    ]
    if not fractions:
        return UNKNOWN_PROGRESS
    return max(0.0, min(sum(fractions) / len(fractions), 1.0))


def live_downloads_of(items: Sequence[DownloadItem]) -> list[QWebEngineDownloadRequest]:
    return [item.download for item in items if item.is_live()]
