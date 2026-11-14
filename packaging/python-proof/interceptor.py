from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

BLOCKED_HOST = "proof.invalid"


class BlockingInterceptor(QWebEngineUrlRequestInterceptor):
    blocked = Signal(str)

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        url = info.requestUrl()
        if url.host() != BLOCKED_HOST:
            return
        info.block(True)
        self.blocked.emit(url.toString())
