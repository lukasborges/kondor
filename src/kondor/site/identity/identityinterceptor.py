from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

from kondor.site.identity.useragents import keeps_client_hints

USER_AGENT_HEADER = b"User-Agent"
CLIENT_HINT_HEADERS = (
    b"Sec-CH-UA",
    b"Sec-CH-UA-Mobile",
    b"Sec-CH-UA-Platform",
    b"Sec-CH-UA-Platform-Version",
    b"Sec-CH-UA-Full-Version-List",
    b"Sec-CH-UA-Arch",
    b"Sec-CH-UA-Bitness",
    b"Sec-CH-UA-Model",
)


class IdentityInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(
        self,
        agents_of: Callable[[], dict[str, str]],
        inner: QWebEngineUrlRequestInterceptor,
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self._agents_of = agents_of
        self._inner = inner

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        self._inner.interceptRequest(info)
        agent = self._agents_of().get(info.firstPartyUrl().host().lower())
        if agent:
            apply_agent(info, agent)


def apply_agent(info: QWebEngineUrlRequestInfo, agent: str) -> None:
    info.setHttpHeader(USER_AGENT_HEADER, agent.encode())
    if keeps_client_hints(agent):
        return
    for header in CLIENT_HINT_HEADERS:
        info.setHttpHeader(header, b"")
