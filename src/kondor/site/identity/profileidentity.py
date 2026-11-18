from PySide6.QtCore import QObject, Signal, qWarning
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.adblock.adblockmanager import AdBlockManager
from kondor.browser.profile import pagescripts
from kondor.site.httpsonly.httpsonlyinterceptor import HttpsOnlyInterceptor
from kondor.site.httpsonly.profilehttpsonly import ProfileHttpsOnly
from kondor.site.identity import identityscript
from kondor.site.identity.identityinterceptor import IdentityInterceptor
from kondor.site.sitesettings import SiteSettings


class ProfileIdentity(QObject):
    changed = Signal()

    def __init__(self, profile: QQuickWebEngineProfile) -> None:
        super().__init__(profile)
        self._profile = profile
        self._session: dict[str, str] = {}
        self._agents: dict[str, str] = {}
        self._script: QWebEngineScript | None = None
        self._interceptor = IdentityInterceptor(self.agents, self._https_only_chain(), self)
        SiteSettings.instance().changed.connect(self.refresh)
        self.refresh()

    def _https_only_chain(self) -> HttpsOnlyInterceptor:
        state = ProfileHttpsOnly(self._profile)
        return HttpsOnlyInterceptor(
            state,
            AdBlockManager.instance().request_filter(),
            self,
        )

    @staticmethod
    def of(profile: QQuickWebEngineProfile | None) -> "ProfileIdentity | None":
        return None if profile is None else profile.findChild(ProfileIdentity)

    def install(self) -> None:
        self._profile.setUrlRequestInterceptor(self._interceptor)

    def agents(self) -> dict[str, str]:
        return self._agents

    def agent_for(self, host: str) -> str:
        return self._agents.get(host, "")

    def set_for_session(self, host: str, agent: str) -> None:
        self._session = {**self._session, host: agent}
        self.refresh()

    def refresh(self) -> None:
        merged = {**SiteSettings.instance().all_user_agents(), **self._session}
        agents = {host: agent for host, agent in merged.items() if agent}
        if agents == self._agents:
            return
        self._agents = agents
        self._replace_script()
        self.changed.emit()

    def _replace_script(self) -> None:
        collection = pagescripts.user_scripts(self._profile)
        script = identityscript.build_script(self._agents)
        if script is None:
            qWarning("Identity script resource not found: browser identity per site is partial")
            return
        if self._script is not None:
            identityscript.remove_script(collection, self._script)
        self._script = script
        pagescripts.insert_script(collection, script)
