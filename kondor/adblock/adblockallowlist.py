from kondor.adblock import adblocksettings


def is_persistent(host: str) -> bool:
    return host in adblocksettings.allow_list()


def with_choice(hosts: list[str], host: str, allowed: bool) -> list[str]:
    if not allowed:
        return [listed for listed in hosts if listed != host]
    return hosts if host in hosts else [*hosts, host]


class AdBlockAllowList:
    def __init__(self) -> None:
        self._session_allowed: set[str] = set()
        self._session_blocked: set[str] = set()

    def is_allowed(self, host: str) -> bool:
        key = host.lower()
        if key in self._session_blocked:
            return False
        return is_persistent(key) or key in self._session_allowed

    def set_persistent(self, host: str, allowed: bool) -> None:
        key = host.lower()
        if not key:
            return
        self._session_allowed.discard(key)
        self._session_blocked.discard(key)
        adblocksettings.set_allow_list(with_choice(adblocksettings.allow_list(), key, allowed))

    def set_for_session(self, host: str, allowed: bool) -> None:
        key = host.lower()
        if not key:
            return
        if allowed:
            self._allow_for_session(key)
        else:
            self._block_for_session(key)

    def hosts(self) -> set[str]:
        persisted = set(adblocksettings.allow_list())
        return (self._session_allowed | persisted) - self._session_blocked

    def _allow_for_session(self, host: str) -> None:
        self._session_allowed.add(host)
        self._session_blocked.discard(host)

    def _block_for_session(self, host: str) -> None:
        self._session_allowed.discard(host)
        if is_persistent(host):
            self._session_blocked.add(host)
