from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.site.identity.profileidentity import ProfileIdentity


class ResponsiveAgent:
    def __init__(self, profile: QQuickWebEngineProfile | None) -> None:
        self._profile = profile
        self._host = ""
        self._agent = ""
        self._previous: str | None = None

    def sync(self, host: str, agent: str) -> bool:
        if (host, agent) == (self._host, self._agent):
            return False
        released = self.release()
        return self._claim(host, agent) or released

    def release(self) -> bool:
        was_applied = self._restore()
        self._host, self._agent, self._previous = "", "", None
        return was_applied

    def _restore(self) -> bool:
        identity = ProfileIdentity.of(self._profile)
        if not self._agent or identity is None:
            return False
        identity.restore_session(self._host, self._previous)
        return True

    def _claim(self, host: str, agent: str) -> bool:
        identity = ProfileIdentity.of(self._profile)
        if not agent or not host or identity is None:
            return False
        self._previous = identity.session_agent(host)
        identity.set_for_session(host, agent)
        self._host, self._agent = host, agent
        return True
