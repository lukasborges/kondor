from collections.abc import Iterator

import pytest
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.app.startup.appstartup import set_up_favicons
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.database import sql
from tests.extensions.pageserver import PageServer

LOAD_TIMEOUT = 30000
PAGE = b'<html><head><link rel="icon" href="/favicon.png"></head><body>page</body></html>'
VIEW_QML = b"""
import QtQuick
import QtWebEngine
WebEngineView {
    property var store
    onIconChanged: if (icon.toString() !== "") store.store(url, icon)
}
"""


def png_bytes() -> bytes:
    image = QImage(16, 16, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.red)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data.data())


@pytest.fixture
def engine(qapp: object, kondor_types: None) -> Iterator[QQmlApplicationEngine]:
    assert sql.run("DELETE FROM favicons") is not None
    engine = QQmlApplicationEngine()
    set_up_favicons(engine)
    yield engine
    FaviconStore.instance().attach_engine(None)


@pytest.fixture
def server() -> PageServer:
    return PageServer({"/": PAGE, "/favicon.png": png_bytes()})


@pytest.fixture
def view(engine: QQmlApplicationEngine) -> Iterator[QQuickItem]:
    component = QQmlComponent(engine)
    component.setData(VIEW_QML, QUrl())
    item = component.createWithInitialProperties({"store": FaviconStore.instance()})
    assert item is not None, component.errorString()
    window = QQuickWindow()
    item.setParentItem(window.contentItem())
    window.show()
    yield item
    item.deleteLater()
    window.close()


def test_stores_the_favicon_of_a_page_loaded_in_a_web_view(
    view: QQuickItem, server: PageServer, qtbot: QtBot
) -> None:
    store = FaviconStore.instance()
    with qtbot.waitSignal(store.revisionChanged, timeout=LOAD_TIMEOUT):
        view.setProperty("url", server.url())
    assert store.hasIcon(server.url())
