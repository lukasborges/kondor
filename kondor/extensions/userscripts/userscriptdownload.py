from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.userscripts.userscriptmetadata import parse_user_script_metadata
from kondor.extensions.userscripts.userscriptpackage import UserScriptSource

BodyHandler = Callable[[bytes], None]


def request_for(url: QUrl) -> QNetworkRequest:
    request = QNetworkRequest(url)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    return request


def is_web_url(url: QUrl) -> bool:
    return url.scheme() in ("https", "http")


def is_fetchable_user_script_url(url: QUrl) -> bool:
    return is_web_url(url) or url.isLocalFile()


class UserScriptDownload(QObject):
    finished = Signal(object, str)

    def __init__(self, network: QNetworkAccessManager, parent: QObject | None) -> None:
        super().__init__(parent)
        self.network = network
        self.source = UserScriptSource()
        self.remaining_bytes = ExtensionPackage.MAX_PACKAGE_BYTES
        self.wants_requirements = True
        self.is_too_large = False

    def start(self, url: QUrl) -> None:
        self.wants_requirements = True
        self.fetch_script(url)

    def start_metadata_only(self, url: QUrl) -> None:
        self.wants_requirements = False
        self.fetch_script(url)

    def fetch_script(self, url: QUrl) -> None:
        self.source.install_url = url
        self.fetch(url, self.accept_script)

    def fetch(self, url: QUrl, handler: BodyHandler) -> None:
        if not is_fetchable_user_script_url(url):
            text = QCoreApplication.translate("UserScript", "Unsupported address: %1")
            self.fail(text.replace("%1", url.toString()))
            return
        reply = self.network.get(request_for(url))
        reply.downloadProgress.connect(lambda received, _total: self.check_size(reply, received))
        reply.finished.connect(lambda: self.receive(reply, handler))

    def check_size(self, reply: QNetworkReply, received: int) -> None:
        self.is_too_large = self.is_too_large or received > self.remaining_bytes
        if self.is_too_large:
            reply.abort()

    def receive(self, reply: QNetworkReply, handler: BodyHandler) -> None:
        reply.deleteLater()
        body = bytes(reply.readAll().data())
        if self.is_too_large:
            self.fail(QCoreApplication.translate("UserScript", "The script is larger than 5 MiB"))
        elif reply.error() != QNetworkReply.NetworkError.NoError:
            self.fail(reply.errorString())
        else:
            self.remaining_bytes -= len(body)
            handler(body)

    def accept_script(self, body: bytes) -> None:
        metadata, error = parse_user_script_metadata(body.decode(errors="replace"))
        if metadata is None:
            self.fail(error)
            return
        self.source.script = body
        self.source.metadata = metadata
        if self.wants_requirements:
            self.fetch_next_requirement()
        else:
            self.succeed()

    def accept_requirement(self, body: bytes) -> None:
        self.source.required_scripts.append(body)
        self.fetch_next_requirement()

    def fetch_next_requirement(self) -> None:
        if self.source.is_complete():
            self.succeed()
            return
        address = self.source.metadata.required_urls[len(self.source.required_scripts)]
        self.fetch(self.source.install_url.resolved(QUrl(address)), self.accept_requirement)

    def succeed(self) -> None:
        self.finished.emit(self.source, "")
        self.deleteLater()

    def fail(self, error: str) -> None:
        self.finished.emit(self.source, error)
        self.deleteLater()
