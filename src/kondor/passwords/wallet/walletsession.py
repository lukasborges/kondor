import os
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from kondor.passwords.wallet.usernamecache import UsernameCache
from kondor.passwords.wallet.walletfolder import WalletFolder
from kondor.passwords.wallet.walletservice import WalletService

DISABLE_VARIABLE = "KONDOR_NO_KWALLET"
AUTOMATIC_BASE = 0


class WalletState(Enum):
    CLOSED = "closed"
    OPENING = "opening"
    OPEN = "open"
    UNAVAILABLE = "unavailable"


def environment_int_value(name: str) -> int:
    try:
        return int(os.environ.get(name, "").strip(), AUTOMATIC_BASE)
    except ValueError:
        return 0


def is_wallet_disabled_by_environment() -> bool:
    return environment_int_value(DISABLE_VARIABLE) != 0


class WalletSession(QObject):
    stateChanged = Signal()
    changed = Signal()

    def __init__(self, service: WalletService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._state = WalletState.CLOSED
        self._handle: int | None = None
        self.usernames = UsernameCache()
        service.opened.connect(self._on_opened)
        service.closed.connect(self._forget_closed_wallet)

    def state(self) -> WalletState:
        return self._state

    def is_open(self) -> bool:
        return self._state is WalletState.OPEN

    def folder(self) -> WalletFolder | None:
        return None if self._handle is None else WalletFolder(self._service, self._handle)

    def open_folder(self) -> WalletFolder | None:
        return self.folder() if self.is_open() else None

    def reload_usernames(self) -> None:
        self.usernames.reload(self.folder())

    def ensure_open(self) -> None:
        if self._state is not WalletState.CLOSED:
            return
        if is_wallet_disabled_by_environment():
            self._set_state(WalletState.UNAVAILABLE)
            return
        self._set_state(WalletState.OPENING)
        if not self._service.open_network_wallet():
            self._set_state(WalletState.UNAVAILABLE)

    def retry(self) -> None:
        if self._state in (WalletState.OPENING, WalletState.OPEN):
            return
        self._handle = None
        self._state = WalletState.CLOSED
        self.ensure_open()

    def _set_state(self, state: WalletState) -> None:
        if self._state is state:
            return
        self._state = state
        self.stateChanged.emit()
        self.changed.emit()

    @Slot(int)
    def _on_opened(self, handle: int) -> None:
        if self._state is not WalletState.OPENING:
            return
        if handle < 0 or not WalletFolder.ensure_exists(self._service, handle):
            self._set_state(WalletState.UNAVAILABLE)
            return
        self._handle = handle
        self.reload_usernames()
        self._set_state(WalletState.OPEN)
        self.changed.emit()

    @Slot()
    def _forget_closed_wallet(self) -> None:
        self._handle = None
        self.usernames.clear()
        self._set_state(WalletState.CLOSED)
