from PySide6.QtCore import QObject
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

from kondor.site.httpsonly.profilehttpsonly import ProfileHttpsOnly
from kondor.site.httpsonly.upgrade import is_upgradable

MAIN_FRAME = QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame


class HttpsOnlyInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(
        self,
        state: ProfileHttpsOnly,
        inner: QWebEngineUrlRequestInterceptor,
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self._state = state
        self._inner = inner

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        self._inner.interceptRequest(info)
        if self._should_upgrade(info):
            info.redirect(self._state.record_upgrade(info.requestUrl()))

    def _should_upgrade(self, info: QWebEngineUrlRequestInfo) -> bool:
        if info.resourceType() != MAIN_FRAME or not self._state.is_enabled():
            return False
        return is_upgradable(info.requestUrl(), self._state.allowed_hosts())
