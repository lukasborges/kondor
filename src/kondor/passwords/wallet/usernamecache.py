from kondor.passwords import passwordorigin
from kondor.passwords.csvimport.passwordimportplan import SavedLogins
from kondor.passwords.wallet.walletfolder import WalletFolder


def sorted_usernames(saved: SavedLogins) -> dict[str, list[str]]:
    return {origin: sorted(logins, key=str.casefold) for origin, logins in saved.items() if logins}


def entry_for(origin: str, username: str) -> dict[str, str]:
    host = passwordorigin.host_of_origin(origin)
    return {"origin": origin, "host": host, "username": username}


class UsernameCache:
    def __init__(self) -> None:
        self._usernames: dict[str, list[str]] = {}

    def reload(self, folder: WalletFolder | None) -> None:
        saved = folder.all_logins() if folder is not None else None
        self._usernames = sorted_usernames(saved or {})

    def clear(self) -> None:
        self._usernames = {}

    def entries(self) -> list[dict[str, str]]:
        return [
            entry_for(origin, name) for origin, names in self._usernames.items() for name in names
        ]

    def usernames(self, origin: str) -> list[str]:
        return list(self._usernames.get(origin, []))

    def has_origin(self, origin: str) -> bool:
        return origin in self._usernames
