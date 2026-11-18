from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.core.settings.settings import Settings
from kondor.site.httpsonly.upgrade import secure_version_of


class ProfileHttpsOnly(QObject):
    upgraded = Signal(QUrl)

    def __init__(self, profile: QQuickWebEngineProfile) -> None:
        super().__init__(profile)
        self._allowed_hosts: set[str] = set()
        self._originals: dict[str, QUrl] = {}

    @staticmethod
    def of(profile: QQuickWebEngineProfile | None) -> "ProfileHttpsOnly | None":
        return None if profile is None else profile.findChild(ProfileHttpsOnly)

    def is_enabled(self) -> bool:
        return bool(Settings.instance().property("httpsOnly"))

    def allowed_hosts(self) -> set[str]:
        return self._allowed_hosts

    def allow(self, host: str) -> None:
        self._allowed_hosts.add(host.lower())

    def record_upgrade(self, original: QUrl) -> QUrl:
        secure = secure_version_of(original)
        self._originals[secure.toString()] = original
        self.upgraded.emit(secure)
        return secure

    def original_of(self, secure: QUrl) -> QUrl:
        return self._originals.get(secure.toString(), QUrl())

    def forget(self, secure: QUrl) -> None:
        self._originals.pop(secure.toString(), None)
