from typing import Any

from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    SLOT,
    QByteArray,
    QGenericArgumentHolder,
    QGenericReturnArgumentHolder,
    QMetaObject,
    QObject,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtDBus import QDBusConnection, QDBusInterface

from kondor.passwords.wallet.walletservice import WalletEntry

SERVICE = "org.kde.kwalletd6"
PATH = "/modules/kwalletd6"
INTERFACE = "org.kde.KWallet"
APPLICATION_ID = "Kondor"
NO_WINDOW = 0
HANDLES_SESSION = True
SUCCESS = 0
SIGNAL_SLOTS = (
    ("walletAsyncOpened", "_on_async_opened(int,int)"),
    ("walletClosedId", "_on_wallet_closed(int)"),
    ("applicationDisconnected", "_on_application_disconnected(QString,QString)"),
)


def as_bytes(value: QByteArray | bytes) -> bytes:
    return bytes(value.data()) if isinstance(value, QByteArray) else value


def application_argument() -> QGenericArgumentHolder:
    return Q_ARG(str, APPLICATION_ID)


def folder_arguments(handle: int, folder: str) -> list[QGenericArgumentHolder]:
    return [Q_ARG(int, handle), Q_ARG(str, folder)]


def entry_arguments(entry: WalletEntry) -> list[QGenericArgumentHolder]:
    return [*folder_arguments(entry.handle, entry.folder), Q_ARG(str, entry.key)]


def open_arguments(wallet: str) -> list[QGenericArgumentHolder]:
    return [
        Q_ARG(str, wallet),
        Q_ARG("qlonglong", NO_WINDOW),
        application_argument(),
        Q_ARG(bool, HANDLES_SESSION),
    ]


class KWalletService(QObject):
    opened = Signal(int)
    closed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._interface: QDBusInterface | None = None
        self._transaction: int | None = None
        self._handle: int | None = None
        self._wallet = ""

    def open_network_wallet(self) -> bool:
        wallet = self._call("networkWallet", Q_RETURN_ARG(str))
        if wallet is None:
            return False
        transaction = self._call("openAsync", Q_RETURN_ARG(int), *open_arguments(wallet))
        if transaction is None or transaction < 0:
            return False
        self._wallet, self._transaction = wallet, transaction
        return True

    def has_folder(self, handle: int, folder: str) -> bool:
        return self._folder_call("hasFolder", handle, folder)

    def create_folder(self, handle: int, folder: str) -> bool:
        return self._folder_call("createFolder", handle, folder)

    def read_map(self, entry: WalletEntry) -> bytes | None:
        arguments = [*entry_arguments(entry), application_argument()]
        data = self._call("readMap", Q_RETURN_ARG(QByteArray), *arguments)
        return None if data is None else as_bytes(data)

    def map_list(self, handle: int, folder: str) -> dict[str, bytes] | None:
        arguments = [*folder_arguments(handle, folder), application_argument()]
        maps = self._call("mapList", Q_RETURN_ARG("QVariantMap"), *arguments)
        return None if maps is None else {key: as_bytes(data) for key, data in maps.items()}

    def entry_list(self, handle: int, folder: str) -> list[str]:
        arguments = [*folder_arguments(handle, folder), application_argument()]
        return list(self._call("entryList", Q_RETURN_ARG("QStringList"), *arguments) or [])

    def write_map(self, entry: WalletEntry, data: bytes) -> bool:
        value = Q_ARG(QByteArray, QByteArray(data))
        arguments = [*entry_arguments(entry), value, application_argument()]
        return bool(self._call("writeMap", Q_RETURN_ARG(int), *arguments) == SUCCESS)

    def remove_entry(self, entry: WalletEntry) -> bool:
        arguments = [*entry_arguments(entry), application_argument()]
        return bool(self._call("removeEntry", Q_RETURN_ARG(int), *arguments) == SUCCESS)

    def _folder_call(self, method: str, handle: int, folder: str) -> bool:
        arguments = [*folder_arguments(handle, folder), application_argument()]
        return self._call(method, Q_RETURN_ARG(bool), *arguments) is True

    def _call(
        self, method: str, result: QGenericReturnArgumentHolder, *arguments: QGenericArgumentHolder
    ) -> Any:
        interface = self._kwallet()
        connection = Qt.ConnectionType.DirectConnection
        try:
            value = QMetaObject.invokeMethod(interface, method, connection, result, *arguments)
        except RuntimeError:
            return None
        return None if interface.lastError().isValid() else value

    def _kwallet(self) -> QDBusInterface:
        if self._interface is None:
            self._interface = QDBusInterface(SERVICE, PATH, INTERFACE, QDBusConnection.sessionBus())
            self._connect_signals()
        return self._interface

    def _connect_signals(self) -> None:
        bus = QDBusConnection.sessionBus()
        for name, slot in SIGNAL_SLOTS:
            bus.connect(SERVICE, PATH, INTERFACE, name, self, SLOT(slot))

    @Slot(int, int)
    def _on_async_opened(self, transaction: int, handle: int) -> None:
        if transaction != self._transaction:
            return
        self._transaction = None
        self._handle = handle if handle >= 0 else None
        self.opened.emit(handle)

    @Slot(int)
    def _on_wallet_closed(self, handle: int) -> None:
        if self._handle is not None and handle == self._handle:
            self._forget_handle()

    @Slot(str, str)
    def _on_application_disconnected(self, wallet: str, application: str) -> None:
        is_ours = wallet == self._wallet and application == APPLICATION_ID
        if self._handle is not None and is_ours:
            self._forget_handle()

    def _forget_handle(self) -> None:
        self._handle = None
        self.closed.emit()
