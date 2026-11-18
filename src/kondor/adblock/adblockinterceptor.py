from PySide6.QtCore import QObject, Signal
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

from kondor.adblock.filters.filterengine import FilterEngine, ResourceKind

ResourceType = QWebEngineUrlRequestInfo.ResourceType
VIEWER_SCHEMES = {"chrome", "chrome-extension"}
RESOURCE_KINDS = {
    ResourceType.ResourceTypeSubFrame: ResourceKind.SUB_FRAME,
    ResourceType.ResourceTypeStylesheet: ResourceKind.STYLESHEET,
    ResourceType.ResourceTypeScript: ResourceKind.SCRIPT,
    ResourceType.ResourceTypeImage: ResourceKind.IMAGE,
    ResourceType.ResourceTypeXhr: ResourceKind.XML_HTTP_REQUEST,
}


def resource_kind_of(resource_type: QWebEngineUrlRequestInfo.ResourceType) -> ResourceKind:
    return RESOURCE_KINDS.get(resource_type, ResourceKind.OTHER)


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    blocked = Signal(str)
    pageStarted = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._engine: FilterEngine | None = None
        self._is_enabled = True
        self._allowed_hosts: set[str] = set()

    def set_engine(self, engine: FilterEngine | None) -> None:
        self._engine = engine

    def set_enabled(self, enabled: bool) -> None:
        self._is_enabled = enabled

    def set_allowed_hosts(self, hosts: set[str]) -> None:
        self._allowed_hosts = set(hosts)

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        if info.resourceType() == ResourceType.ResourceTypeMainFrame:
            self.pageStarted.emit(info.requestUrl().host().lower())
        elif self._is_enabled:
            self._block_if_listed(info)

    def _block_if_listed(self, info: QWebEngineUrlRequestInfo) -> None:
        first_party = info.firstPartyUrl().host().lower()
        if not self._is_listed(info, first_party):
            return
        info.block(True)
        self.blocked.emit(first_party)

    def _is_listed(self, info: QWebEngineUrlRequestInfo, first_party_host: str) -> bool:
        if info.requestUrl().scheme() in VIEWER_SCHEMES:
            return False
        engine = self._engine_unless_allowed(first_party_host)
        kind = resource_kind_of(info.resourceType())
        return engine is not None and engine.should_block(info.requestUrl(), first_party_host, kind)

    def _engine_unless_allowed(self, first_party_host: str) -> FilterEngine | None:
        if first_party_host in self._allowed_hosts:
            return None
        return self._engine
