from PySide6.QtCore import QObject, QTimer, Signal

from kondor.passwords.wallet.walletservice import WalletEntry

HANDLE = 7
FAILED_HANDLE = -1


class FakeWallet(QObject):
    opened = Signal(int)
    closed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.folders: dict[str, dict[str, bytes]] = {}
        self.can_open = True
        self.can_create_folder = True
        self.can_write = True
        self.open_requests = 0

    def open_network_wallet(self) -> bool:
        self.open_requests += 1
        handle = HANDLE if self.can_open else FAILED_HANDLE
        QTimer.singleShot(0, self, lambda: self.opened.emit(handle))
        return True

    def close(self) -> None:
        self.closed.emit()

    def has_folder(self, handle: int, folder: str) -> bool:
        return folder in self.folders

    def create_folder(self, handle: int, folder: str) -> bool:
        if self.can_create_folder:
            self.folders[folder] = {}
        return self.can_create_folder

    def remove_folder(self, handle: int, folder: str) -> bool:
        return self.folders.pop(folder, None) is not None

    def read_map(self, entry: WalletEntry) -> bytes | None:
        return self.folders[entry.folder].get(entry.key, b"")

    def map_list(self, handle: int, folder: str) -> dict[str, bytes] | None:
        return dict(self.folders[folder])

    def entry_list(self, handle: int, folder: str) -> list[str]:
        return list(self.folders[folder])

    def write_map(self, entry: WalletEntry, data: bytes) -> bool:
        if self.can_write:
            self.folders[entry.folder][entry.key] = data
        return self.can_write

    def remove_entry(self, entry: WalletEntry) -> bool:
        return self.folders[entry.folder].pop(entry.key, None) is not None
