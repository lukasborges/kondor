from PySide6.QtCore import (
    QCoreApplication,
    QCryptographicHash,
    QDir,
    QFile,
    QIODevice,
    QObject,
    QTemporaryFile,
    Signal,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from kondor.extensions.catalog.catalogentry import CONTEXT, CatalogEntry
from kondor.extensions.package.packagelimits import MAX_PACKAGE_BYTES

TEMPLATE = "/kondor-extension-XXXXXX.kondorext"
NO_TEMPORARY_FILE = "Cannot create a temporary file"
TOO_LARGE = "The package is larger than expected"
UNREADABLE = "Cannot read the downloaded package"
BAD_CHECKSUM = "The downloaded package does not match its checksum"


def request_for(entry: CatalogEntry) -> QNetworkRequest:
    request = QNetworkRequest(entry.package)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    return request


def limit_for(entry: CatalogEntry) -> int:
    return min(entry.size, MAX_PACKAGE_BYTES) if entry.size > 0 else MAX_PACKAGE_BYTES


def translated(text: str) -> str:
    return str(QCoreApplication.translate(CONTEXT, text))


def sha256_hex_of(path: str) -> str | None:
    check = QFile(path)
    if not check.open(QIODevice.OpenModeFlag.ReadOnly):
        return None
    digest = QCryptographicHash(QCryptographicHash.Algorithm.Sha256)
    digest.addData(check)
    return bytes(digest.result().toHex().data()).decode()


class PackageDownload(QObject):
    finished = Signal(str, str)

    def __init__(self, network: QNetworkAccessManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.network = network
        self.file = QTemporaryFile(QDir.tempPath() + TEMPLATE)
        self.file.setAutoRemove(False)
        self.reply: QNetworkReply | None = None
        self.limit = MAX_PACKAGE_BYTES
        self.expected_hash = ""
        self.received = 0
        self.failure = ""

    def start(self, entry: CatalogEntry) -> None:
        self.reply = self.network.get(request_for(entry))
        self.limit = limit_for(entry)
        self.expected_hash = entry.sha256
        if not self.file.open():
            self.abandon(translated(NO_TEMPORARY_FILE))
            return
        self.reply.readyRead.connect(self.receive)
        self.reply.finished.connect(self.complete)

    def abandon(self, message: str) -> None:
        if self.reply is not None:
            self.reply.abort()
            self.reply.deleteLater()
        self.finish_with("", message)

    def receive(self) -> None:
        assert self.reply is not None
        chunk = bytes(self.reply.readAll().data())
        self.received += len(chunk)
        if self.received <= self.limit:
            self.file.write(chunk)
            return
        self.failure = translated(TOO_LARGE)
        self.reply.abort()

    def checksum_error(self) -> str:
        actual = sha256_hex_of(self.file.fileName())
        if actual is None:
            return translated(UNREADABLE)
        return "" if actual == self.expected_hash else translated(BAD_CHECKSUM)

    def failure_of(self) -> str:
        assert self.reply is not None
        if self.failure:
            return self.failure
        if self.reply.error() != QNetworkReply.NetworkError.NoError:
            return str(self.reply.errorString())
        return self.checksum_error()

    def complete(self) -> None:
        assert self.reply is not None
        self.reply.deleteLater()
        self.file.write(self.reply.readAll())
        self.file.close()
        error = self.failure_of()
        if error:
            QFile.remove(self.file.fileName())
        self.finish_with("" if error else self.file.fileName(), error)

    def finish_with(self, path: str, error: str) -> None:
        self.finished.emit(path, error)
        self.deleteLater()
