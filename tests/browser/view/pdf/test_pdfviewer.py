from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QUrl
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from kondor.downloads.downloadmanager import DownloadManager
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

LOAD_TIMEOUT = 30000
SETTLE_MILLISECONDS = 1500
PDF = (
    b"%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)
EMBED_PAGE = b'<html><body><embed src="/x.pdf" type="application/pdf"></body></html>'
TAB_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    id: holder
    width: 400; height: 300
    property int loadsSucceeded: 0
    function findPageView(item) {
        if (item.objectName === "pageView")
            return item
        for (const child of item.children) {
            const found = findPageView(child)
            if (found)
                return found
        }
        return null
    }
    function loadInPageView(url) { findPageView(holder).url = url }
    Component.onCompleted: {
        findPageView(holder).loadingChanged.connect((info) => {
            if (info.status === WebEngineView.LoadSucceededStatus) holder.loadsSucceeded++
        })
    }
    WebViewTab {
        anchors.fill: parent
        tab: testTab
        tabModel: testModel
        browserActions: null
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

    def url(self, path: str = "x.pdf") -> str:
        return f"http://127.0.0.1:{self.server.serverPort()}/{path}"

    def accept(self) -> None:
        while (socket := self.server.nextPendingConnection()) is not None:
            socket.readyRead.connect(lambda socket=socket: self.respond(socket))
            socket.disconnected.connect(socket.deleteLater)

    def respond(self, socket: QTcpSocket) -> None:
        request = bytes(socket.readAll().data()).decode(errors="replace")
        if request.startswith("GET /embed.html"):
            self.send(socket, "text/html", EMBED_PAGE)
        else:
            self.send(socket, "application/pdf", PDF)

    def send(self, socket: QTcpSocket, kind: str, body: bytes) -> None:
        extra = f"Content-Disposition: {self.disposition}\r\n" if self.disposition else ""
        head = f"HTTP/1.1 200 OK\r\nContent-Type: {kind}\r\n{extra}"
        head += f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
        socket.write(head.encode() + body)
        socket.disconnectFromHost()


class Scene:
    def __init__(self, engine: QQmlEngine, private: bool, download_directory: Path) -> None:
        profiles = ProfileManager.instance()
        self.profile = profiles.createPrivateProfile() if private else profiles.defaultProfile()
        self.profile.setDownloadPath(str(download_directory))
        self.model = TabModel()
        self.tab = Tab(self.profile)
        engine.rootContext().setContextProperty("testTab", self.tab)
        engine.rootContext().setContextProperty("testModel", self.model)
        self.component = load_component(engine, TAB_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.window.resize(400, 300)
        self.root.setParentItem(self.window.contentItem())  # type: ignore[attr-defined]
        self.window.show()
        self.started = 0
        DownloadManager.instance().downloadStarted.connect(self.count_download)

    def count_download(self) -> None:
        self.started += 1

    def load(self, url: str) -> None:
        QMetaObject.invokeMethod(self.root, "loadInPageView", Q_ARG("QVariant", url))

    def loads_succeeded(self) -> int:
        return int(self.root.property("loadsSucceeded"))

    def release(self) -> None:
        DownloadManager.instance().downloadStarted.disconnect(self.count_download)
        self.window.close()
        release(self.root)
        release(self.window, self.component, self.tab, self.model)
        self.clear_downloads()

    def clear_downloads(self) -> None:
        model = DownloadManager.instance().download_model()
        while model.rowCount() > 0:
            model.remove_download(0)


@pytest.fixture(params=[False, True], ids=["normal", "private"])
def scene(
    request: pytest.FixtureRequest, kondor_engine: QQmlEngine, tmp_path: Path
) -> Iterator[Scene]:
    settings = Settings.instance()
    previous = settings.property("downloadDirectory")
    settings.setProperty("downloadDirectory", str(tmp_path))
    created = Scene(kondor_engine, private=bool(request.param), download_directory=tmp_path)
    yield created
    created.release()
    settings.setProperty("downloadDirectory", previous)


def test_pdf_opens_in_the_page_view_without_a_download(scene: Scene, qtbot: QtBot) -> None:
    server = PdfServer(None)
    scene.load(server.url())
    qtbot.waitUntil(lambda: scene.loads_succeeded() == 1, timeout=LOAD_TIMEOUT)
    qtbot.wait(SETTLE_MILLISECONDS)
    assert scene.started == 0


def test_attachment_pdf_reaches_the_download_manager(scene: Scene, qtbot: QtBot) -> None:
    server = PdfServer("attachment")
    scene.load(server.url())
    qtbot.waitUntil(lambda: scene.started == 1, timeout=LOAD_TIMEOUT)


def test_local_pdf_file_opens_in_the_page_view(scene: Scene, qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "local.pdf"
    path.write_bytes(PDF)
    scene.load(QUrl.fromLocalFile(str(path)).toString())
    qtbot.waitUntil(lambda: scene.loads_succeeded() == 1, timeout=LOAD_TIMEOUT)
    assert scene.started == 0


def test_embedded_pdf_opens_in_the_page_view(scene: Scene, qtbot: QtBot) -> None:
    server = PdfServer(None)
    scene.load(server.url("embed.html"))
    qtbot.waitUntil(lambda: scene.loads_succeeded() >= 1, timeout=LOAD_TIMEOUT)
    qtbot.wait(SETTLE_MILLISECONDS)
    assert scene.started == 0
