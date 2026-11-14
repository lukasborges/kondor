from PySide6.QtCore import QObject


class CertificateOverrides:
    def __init__(self) -> None:
        self._hosts_by_profile: dict[int, set[str]] = {}

    def mark(self, profile: QObject | None, host: str) -> None:
        if profile is None or not host:
            return
        self._hosts_by_profile.setdefault(id(profile), set()).add(host.lower())

    def is_overridden(self, profile: QObject | None, host: str) -> bool:
        if profile is None or not host:
            return False
        return host.lower() in self._hosts_by_profile.get(id(profile), set())

    def forget(self, profile: QObject) -> None:
        self._hosts_by_profile.pop(id(profile), None)
