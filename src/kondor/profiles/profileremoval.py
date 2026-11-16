import shutil
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, QSettings, qWarning

from kondor.passwords.wallet.kwalletservice import KWalletService
from kondor.passwords.wallet.walletservice import WalletService
from kondor.passwords.wallet.walletsession import is_wallet_disabled_by_environment
from kondor.profiles import profilepaths
from kondor.profiles.activeprofile import ORGANIZATION


class WalletFolderRemoval(QObject):
    def __init__(self, service: WalletService, folder: str) -> None:
        super().__init__(QCoreApplication.instance())
        self._service = service
        self._folder = folder
        service.opened.connect(self._on_opened)

    def start(self) -> None:
        if is_wallet_disabled_by_environment() or not self._service.open_network_wallet():
            self._give_up()

    def _on_opened(self, handle: int) -> None:
        if handle < 0:
            self._give_up()
            return
        if self._service.has_folder(handle, self._folder):
            self._remove(handle)
        self.deleteLater()

    def _remove(self, handle: int) -> None:
        if not self._service.remove_folder(handle, self._folder):
            qWarning(f"Kondor: cannot remove the wallet folder {self._folder}")

    def _give_up(self) -> None:
        qWarning(f"Kondor: the wallet is unavailable, keeping the wallet folder {self._folder}")
        self.deleteLater()


def settings_file(profile_id: str) -> Path:
    application = profilepaths.settings_application(profile_id)
    return Path(QSettings(ORGANIZATION, application).fileName())


def remove_directory(path: Path) -> bool:
    shutil.rmtree(path, ignore_errors=True)
    return not path.exists()


def remove_file(path: Path) -> bool:
    path.unlink(missing_ok=True)
    return not path.exists()


def remove_wallet_folder(profile_id: str, service: WalletService | None) -> None:
    folder = profilepaths.wallet_folder(profile_id)
    WalletFolderRemoval(service or KWalletService(), folder).start()


def remove_profile_data(profile_id: str, service: WalletService | None = None) -> bool:
    if profilepaths.is_default(profile_id):
        return False
    directories = [
        profilepaths.data_directory(profile_id),
        *profilepaths.web_data_directories(profile_id),
    ]
    removed = [remove_directory(path) for path in directories]
    removed.append(remove_file(settings_file(profile_id)))
    remove_wallet_folder(profile_id, service)
    return all(removed)
