from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

BLOCKED_HOST = "proof.invalid"


class BlockingInterceptor(QWebEngineUrlRequestInterceptor):
    blocked = Signal(str)

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        url = info.requestUrl().toString()
        if BLOCKED_HOST not in url:
            return
        info.block(True)
        self.blocked.emit(url)
