import pytest
from PySide6.QtCore import QObject, Slot
from PySide6.QtDBus import QDBusError

from kondor.passwords.wallet import kwalletservice
from kondor.passwords.wallet.kwalletservice import KWalletService
from kondor.passwords.wallet.walletsession import WalletSession, WalletState

TRANSACTION = 7
HANDLE = 3


class MissingInterface(QObject):
    def isValid(self) -> bool:
        return False

    def lastError(self) -> QDBusError:
        return QDBusError()


class AvailableInterface(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def isValid(self) -> bool:
        return True

    def lastError(self) -> QDBusError:
        return QDBusError()

    @Slot(result=str)
    def networkWallet(self) -> str:
        self.calls.append("networkWallet")
        return "kdewallet"

    @Slot(str, "qlonglong", str, bool, result=int)
    def openAsync(self, *_arguments: object) -> int:
        self.calls.append("openAsync")
        return TRANSACTION

    @Slot(int, str, str, result=bool)
    def hasFolder(self, _handle: int, _folder: str, _application: str) -> bool:
        return True


class FakeBus:
    def __init__(self) -> None:
        self.available = AvailableInterface()
        self.is_service_running = False

    def create_interface(self, *_arguments: object) -> QObject:
        return self.available if self.is_service_running else MissingInterface()


@pytest.fixture
def bus(monkeypatch: pytest.MonkeyPatch) -> FakeBus:
    monkeypatch.delenv("KONDOR_NO_KWALLET")
    fake_bus = FakeBus()
    monkeypatch.setattr(kwalletservice, "QDBusInterface", fake_bus.create_interface)
    return fake_bus


def test_retry_opens_the_wallet_once_the_service_is_available(bus: FakeBus) -> None:
    service = KWalletService()
    session = WalletSession(service)
    session.ensure_open()
    assert session.state() is WalletState.UNAVAILABLE
    bus.is_service_running = True
    session.retry()
    service._on_async_opened(TRANSACTION, HANDLE)
    assert session.is_open()
    assert bus.available.calls == ["networkWallet", "openAsync"]


def test_keeps_a_valid_interface(bus: FakeBus) -> None:
    bus.is_service_running = True
    service = KWalletService()
    assert service._kwallet() is service._kwallet()
