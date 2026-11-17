from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.tabs.features.tabpopups import host_of
from kondor.site.identity import useragents
from kondor.site.identity.profileidentity import ProfileIdentity
from kondor.site.sitesettings import SiteSettings


class TabIdentity(QObject):
    hostChanged = Signal()
    choiceChanged = Signal()
    reloadPendingChanged = Signal()

    def __init__(
        self, profile: QQuickWebEngineProfile | None, is_private: bool, parent: QObject
    ) -> None:
        super().__init__(parent)
        self._profile = profile
        self._is_private = is_private
        self._host = ""
        self._choice = useragents.KONDOR
        self._is_reload_pending = False
        identity = ProfileIdentity.of(profile)
        if identity is not None:
            identity.changed.connect(self._refresh_choice)

    host = Property(str, lambda self: self._host, notify=hostChanged)
    choice = Property(str, lambda self: self._choice, notify=choiceChanged)
    isReloadPending = Property(
        bool, lambda self: self._is_reload_pending, notify=reloadPendingChanged
    )

    @Property(str, notify=choiceChanged)
    def currentAgent(self) -> str:
        identity = ProfileIdentity.of(self._profile)
        return "" if identity is None else identity.agent_for(self._host)

    @Property(str, constant=True)
    def defaultAgent(self) -> str:
        return "" if self._profile is None else self._profile.httpUserAgent()

    def update_for(self, url: QUrl) -> None:
        host = host_of(url)
        if host == self._host:
            return
        self._host = host
        self.hostChanged.emit()
        self._refresh_choice()

    @Slot(str)
    def choose(self, choice: str) -> None:
        self.setAgent(useragents.agent_for_choice(choice, self.defaultAgent))

    @Slot(str)
    def setAgent(self, agent: str) -> None:
        identity = ProfileIdentity.of(self._profile)
        if not self._host or identity is None or agent == self.currentAgent:
            return
        self._store(identity, agent)
        self._set_reload_pending(True)

    @Slot()
    def dismiss(self) -> None:
        self._set_reload_pending(False)

    def _store(self, identity: ProfileIdentity, agent: str) -> None:
        if self._is_private:
            identity.set_for_session(self._host, agent)
        else:
            SiteSettings.instance().setUserAgent(self._host, agent)

    def _set_reload_pending(self, is_pending: bool) -> None:
        if is_pending == self._is_reload_pending:
            return
        self._is_reload_pending = is_pending
        self.reloadPendingChanged.emit()

    def _refresh_choice(self) -> None:
        choice = useragents.choice_of(self.currentAgent)
        if choice == self._choice:
            return
        self._choice = choice
        self.choiceChanged.emit()
