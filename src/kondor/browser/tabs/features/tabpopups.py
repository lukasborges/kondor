from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from kondor.browser.popups.popupurl import is_web_address
from kondor.core.settings.settings import Settings
from kondor.site.sitesettings import SiteSettings

MAX_BLOCKED = 10
BLOCK_SETTING = "blockPopups"


def host_of(url: QUrl) -> str:
    return url.host().lower() if is_web_address(url) else ""


def is_blocking_enabled() -> bool:
    return bool(Settings.instance().property(BLOCK_SETTING))


def with_newest_first(urls: list[str], url: str) -> list[str]:
    return [url, *(listed for listed in urls if listed != url)][:MAX_BLOCKED]


class TabPopups(QObject):
    blockedChanged = Signal()
    hostChanged = Signal()
    allowedChanged = Signal()
    openRequested = Signal(str)

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._blocked: list[str] = []
        self._host = ""
        self._is_allowed = False
        SiteSettings.instance().changed.connect(self._on_site_settings_changed)

    blockedUrls = Property("QStringList", lambda self: list(self._blocked), notify=blockedChanged)
    host = Property(str, lambda self: self._host, notify=hostChanged)
    isAllowed = Property(bool, lambda self: self._is_allowed, notify=allowedChanged)
    canChangeAllowed = Property(bool, lambda self: not self._is_private, constant=True)

    def update_for(self, url: QUrl) -> None:
        host = host_of(url)
        if host == self._host:
            return
        self._host = host
        self.hostChanged.emit()
        self._refresh_allowed()

    def add_blocked(self, url: str) -> None:
        if self._is_allowed or not is_blocking_enabled():
            return
        self._blocked = with_newest_first(self._blocked, url)
        self.blockedChanged.emit()

    @Slot()
    def clear(self) -> None:
        if not self._blocked:
            return
        self._blocked = []
        self.blockedChanged.emit()

    @Slot(str)
    def openBlocked(self, url: str) -> None:
        if url not in self._blocked:
            return
        self._blocked.remove(url)
        self.blockedChanged.emit()
        self.openRequested.emit(url)

    @Slot(bool)
    def setAllowed(self, allowed: bool) -> None:
        if self._is_private or not self._host:
            return
        SiteSettings.instance().setPopupsAllowed(self._host, allowed)

    @Slot(str)
    def _on_site_settings_changed(self, _host: str) -> None:
        self._refresh_allowed()

    def _refresh_allowed(self) -> None:
        allowed = bool(self._host) and SiteSettings.instance().popupsAllowed(self._host)
        if allowed == self._is_allowed:
            return
        self._is_allowed = allowed
        self.allowedChanged.emit()
