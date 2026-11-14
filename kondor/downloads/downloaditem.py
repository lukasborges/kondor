from dataclasses import dataclass, field

import shiboken6
from PySide6.QtCore import QObject
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from kondor.downloads.transferspeed import TransferSpeed


@dataclass
class DownloadItem:
    watcher: QObject | None
    download: QWebEngineDownloadRequest
    is_private: bool = False
    speed: TransferSpeed = field(default_factory=TransferSpeed)

    def release_watcher(self) -> None:
        self.watcher = None

    def is_live(self) -> bool:
        return bool(shiboken6.isValid(self.download))
