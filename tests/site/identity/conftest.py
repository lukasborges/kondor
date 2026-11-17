from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QTcpSocket
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.site.identity.profileidentity import ProfileIdentity
from tests.extensions.pageserver import PageServer, http_response, requested_path
from tests.qmlsupport import error_text, load_component, release

LOAD_TIMEOUT = 30000
SIZE = 300
SETTLE_MS = 500
PAGE = b"""<html><head><title>loading</title></head><body><script>
document.title = navigator.userAgent + "|" + (navigator.userAgentData ? "hints" : "nohints");
</script></body></html>"""
FRAME = b"<script>parent.postMessage(navigator.userAgent, '*');</script>"
OUTER = b"""<html><head><title>loading</title></head><body>
<iframe src=""></iframe><script>
addEventListener("message", event => { document.title = event.data + "|frame"; });
document.querySelector("iframe").src = location.origin.replace("127.0.0.1", "localhost") + "/frame";
</script></body></html>"""
SCENE_QML = """
import QtQuick
import Kondor

Item {
    width: 300
    height: 300
    Repeater {
        model: testTabModel
        delegate: WebViewTab {
            width: 300
            height: 300
            tabModel: testTabModel
            browserActions: ({})
        }
    }
}
"""


class EchoServer(PageServer):
    def __init__(self) -> None:
        super().__init__({"/": PAGE, "/outer": OUTER, "/frame": FRAME})
        self.headers: list[dict[str, str]] = []
        self.page_headers: list[dict[str, str]] = []

    def respond(self, socket: QTcpSocket) -> None:
        request = bytes(socket.readAll().data()).decode(errors="replace")
        lines = request.split("\r\n")[1:]
        pairs = (line.split(": ", 1) for line in lines if ": " in line)
        headers = {name.lower(): value for name, value in pairs}
        self.headers.append(headers)
        path = requested_path(request.encode())
        if path in ("/", "/outer"):
            self.page_headers.append(headers)
        socket.write(http_response("200 OK", self.bodies.get(path, PAGE)))
        socket.disconnectFromHost()


def forget_identities_of_earlier_tests() -> None:
    identity = ProfileIdentity.of(ProfileManager.instance().defaultProfile())
    assert identity is not None
    identity.refresh()


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    forget_identities_of_earlier_tests()
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


@pytest.fixture
def window(model: TabModel, kondor_engine: QQmlEngine) -> Iterator[QQuickWindow]:
    kondor_engine.rootContext().setContextProperty("testTabModel", model)
    component = load_component(kondor_engine, SCENE_QML)
    item = component.create()
    assert item is not None, error_text(component)
    assert isinstance(item, QQuickItem)
    quick_window = QQuickWindow()
    quick_window.resize(SIZE, SIZE)
    item.setParentItem(quick_window.contentItem())
    quick_window.show()
    yield quick_window
    quick_window.close()
    item.deleteLater()


@pytest.fixture
def server() -> Iterator[EchoServer]:
    echo_server = EchoServer()
    yield echo_server
    release(echo_server)


class Browser:
    def __init__(self, model: TabModel, server: EchoServer, qtbot: QtBot) -> None:
        self.model = model
        self.server = server
        self.qtbot = qtbot

    def open_page(self, url: QUrl, is_private: bool = False) -> Tab:
        tab = self.model.addTab(is_private)
        assert tab is not None
        tab.navigateTo(url)
        self.wait_for_page(tab)
        return tab

    def wait_for_page(self, tab: Tab) -> None:
        self.qtbot.waitUntil(lambda: "|" in tab.title, timeout=LOAD_TIMEOUT)

    def reload(self, tab: Tab) -> None:
        tab.setTitle("")
        tab.reload()
        self.wait_for_page(tab)

    def last_header(self, name: str) -> str:
        return self.server.page_headers[-1].get(name, "")


@pytest.fixture
def browser(model: TabModel, server: EchoServer, qtbot: QtBot) -> Iterator[Browser]:
    yield Browser(model, server, qtbot)
    qtbot.wait(SETTLE_MS)
