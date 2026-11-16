import subprocess
import sys
import uuid

import pytest
from PySide6.QtCore import QCoreApplication

from kondor.passwords.wallet import kwalletservice
from kondor.passwords.wallet.kwalletservice import KWalletService
from kondor.passwords.wallet.walletsession import WalletSession, WalletState

PROVIDER = """
import sys
from PySide6.QtCore import QCoreApplication, QObject, Slot, QTimer
from PySide6.QtDBus import QDBusConnection

class Wallet(QObject):
    @Slot(result=str)
    def networkWallet(self):
        return "kdewallet"

    @Slot(str, "qlonglong", str, bool, result=int)
    def openAsync(self, *arguments):
        print("openAsync", flush=True)
        return 7

app = QCoreApplication([])
bus = QDBusConnection.sessionBus()
wallet = Wallet()
option = QDBusConnection.RegisterOption.ExportAllSlots
bus.registerObject("/modules/kwalletd6", "org.kde.KWallet", wallet, option)
bus.registerService(sys.argv[1])
print("ready", flush=True)
QTimer.singleShot(20000, app.quit)
app.exec()
"""


def wait_for_events(milliseconds: int) -> None:
    QCoreApplication.processEvents()
    QCoreApplication.instance().thread().msleep(milliseconds)
    QCoreApplication.processEvents()


@pytest.fixture
def service_name(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.delenv("KONDOR_NO_KWALLET", raising=False)
    name = f"org.kondor.test{uuid.uuid4().hex}"
    monkeypatch.setattr(kwalletservice, "SERVICE", name)
    return name


def test_retry_calls_a_service_registered_after_the_interface_was_built(
    service_name: str,
) -> None:
    QCoreApplication.instance() or QCoreApplication([])
    session = WalletSession(KWalletService())
    session.ensure_open()
    assert session.state() is WalletState.UNAVAILABLE
    command = [sys.executable, "-I", "-c", PROVIDER, service_name]
    provider = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    try:
        assert provider.stdout is not None
        provider.stdout.readline()
        wait_for_events(500)
        session.retry()
        assert provider.stdout.readline().strip() == "openAsync"
    finally:
        provider.kill()
