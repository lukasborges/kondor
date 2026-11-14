from kondor.passwords.wallet.walletfolder import WalletFolder
from kondor.passwords.wallet.walletmap import qmap_order
from kondor.passwords.wallet.walletsession import WalletSession


def write_or_remove(folder: WalletFolder, origin: str, logins: dict[str, str]) -> None:
    if logins:
        folder.write_logins(origin, logins)
    else:
        folder.remove_origin(origin)


class WalletLogins:
    def __init__(self, session: WalletSession) -> None:
        self._session = session

    def password(self, origin: str, username: str) -> str:
        folder = self._session.open_folder()
        if folder is None:
            return ""
        return (folder.logins(origin) or {}).get(username, "")

    def credentials_for(self, origin: str) -> list[dict[str, str]]:
        folder = self._session.open_folder()
        if folder is None or not self._session.usernames.has_origin(origin):
            return []
        logins = folder.logins(origin) or {}
        names = sorted(logins, key=qmap_order)
        return [{"username": name, "password": logins[name]} for name in names]

    def save(self, origin: str, username: str, password: str) -> bool:
        folder = self._session.open_folder()
        if folder is None or not origin:
            return False
        logins = folder.logins(origin) or {}
        logins[username] = password
        return folder.write_logins(origin, logins)

    def remove(self, origin: str, username: str) -> bool:
        folder = self._session.open_folder()
        logins = folder.logins(origin) if folder is not None else None
        if folder is None or logins is None or username not in logins:
            return False
        del logins[username]
        write_or_remove(folder, origin, logins)
        return True
