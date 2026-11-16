from kondor.passwords.csvimport.passwordimportplan import SavedLogins
from kondor.passwords.wallet.walletmap import map_from_bytes, map_to_bytes
from kondor.passwords.wallet.walletservice import WalletEntry, WalletService
from kondor.profiles.activeprofile import ActiveProfile


class WalletFolder:
    def __init__(self, service: WalletService, handle: int) -> None:
        self._service = service
        self._handle = handle

    @staticmethod
    def ensure_exists(service: WalletService, handle: int) -> bool:
        folder = ActiveProfile.wallet_folder()
        return service.has_folder(handle, folder) or service.create_folder(handle, folder)

    def logins(self, origin: str) -> dict[str, str] | None:
        data = self._service.read_map(self._entry(origin))
        return None if data is None else map_from_bytes(data)

    def all_logins(self) -> SavedLogins | None:
        maps = self._service.map_list(self._handle, ActiveProfile.wallet_folder())
        if maps is None:
            return None
        return {origin: map_from_bytes(data) for origin, data in maps.items()}

    def write_logins(self, origin: str, logins: dict[str, str]) -> bool:
        return self._service.write_map(self._entry(origin), map_to_bytes(logins))

    def remove_origin(self, origin: str) -> bool:
        return self._service.remove_entry(self._entry(origin))

    def origins(self) -> list[str]:
        return self._service.entry_list(self._handle, ActiveProfile.wallet_folder())

    def _entry(self, origin: str) -> WalletEntry:
        return WalletEntry(self._handle, ActiveProfile.wallet_folder(), origin)
