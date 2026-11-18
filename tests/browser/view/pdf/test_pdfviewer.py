from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

LOAD_TIMEOUT = 30000
PDF = (
    b"%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)
SCENE_QML = """
import QtQuick
import QtWebEngine

Item {
    id: scene
    width: 400; height: 300
    property int downloads: 0
    property int loadsSucceeded: 0
    WebEngineView {
        id: view
        objectName: "view"
        anchors.fill: parent
        settings.pluginsEnabled: true
        settings.pdfViewerEnabled: true
        profile: WebEngineProfile {
            offTheRecord: true
            onDownloadRequested: (download) => { scene.downloads++; download.cancel() }
        }
        onLoadingChanged: (info) => {
            if (info.status === WebEngineLoadingInfo.LoadSucceededStatus) scene.loadsSucceeded++
        }
    }
}
"""


class PdfServer(QObject):
    def __init__(self, disposition: str | None) -> None:
        super().__init__()
        self.disposition = disposition
        self.server = QTcpServer(self)
        self.server.listen(QHostAddress.SpecialAddress.LocalHost, 0)
        self.server.newConnection.connect(self.accept)

    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.serverPort()}/x.pdf"

    def accept(self) -> None:
        while (socket := self.server.nextPendingConnection()) is not None:
            socket.readyRead.connect(lambda socket=socket: self.respond(socket))
            socket.disconnected.connect(socket.deleteLater)

    def respond(self, socket: QTcpSocket) -> None:
        socket.readAll()
        extra = f"Content-Disposition: {self.disposition}\r\n" if self.disposition else ""
        head = f"HTTP/1.1 200 OK\r\nContent-Type: application/pdf\r\n{extra}"
        head += f"Content-Length: {len(PDF)}\r\nConnection: close\r\n\r\n"
        socket.write(head.encode() + PDF)
        socket.disconnectFromHost()


class Scene:
    def __init__(self, engine: QQmlEngine) -> None:
        self.component = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.window.resize(400, 300)
        self.root.setParentItem(self.window.contentItem())
        self.window.show()

    def load(self, url: str) -> None:
        view = self.root.findChild(QObject, "view")
        assert view is not None
        view.setProperty("url", url)

    def downloads(self) -> int:
        return int(self.root.property("downloads"))

    def loads_succeeded(self) -> int:
        return int(self.root.property("loadsSucceeded"))

    def release(self) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)


@pytest.fixture
def scene(kondor_engine: QQmlEngine) -> Iterator[Scene]:
    created = Scene(kondor_engine)
    yield created
    created.release()


def test_pdf_opens_in_the_view_without_a_download(scene: Scene, qtbot: QtBot) -> None:
    server = PdfServer(None)
    scene.load(server.url())
    qtbot.waitUntil(lambda: scene.loads_succeeded() == 1, timeout=LOAD_TIMEOUT)
    assert scene.downloads() == 0


def test_attachment_pdf_is_downloaded(scene: Scene, qtbot: QtBot) -> None:
    server = PdfServer("attachment")
    scene.load(server.url())
    qtbot.waitUntil(lambda: scene.downloads() == 1, timeout=LOAD_TIMEOUT)
