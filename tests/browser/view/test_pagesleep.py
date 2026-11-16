from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from tests.extensions.pageserver import PageServer
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

LOAD_TIMEOUT = 30000
SETTLE_MILLISECONDS = 1500
DISCARDED = 2
ACTIVE = 0
FORM_PAGE = b"<html><head><title>form</title></head><body><input id='q'></body></html>"
SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    id: scene
    width: 400; height: 300
    property bool loaded: false
    readonly property int lifecycle: view.lifecycleState
    WebEngineView {
        id: view
        objectName: "view"
        anchors.fill: parent
        profile: testTab.profile
        onLoadingChanged: function(info) {
            if (info.status === WebEngineLoadingInfo.LoadSucceededStatus) scene.loaded = true
        }
    }
    PageSleep { tab: testTab; webView: view }
}
"""


class Scene:
    def __init__(self, engine: QQmlEngine, tab: Tab) -> None:
        engine.rootContext().setContextProperty("testTab", tab)
        self.component: QQmlComponent = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.window.resize(400, 300)
        self.root.setParentItem(self.window.contentItem())  # type: ignore[attr-defined]
        self.window.show()

    @property
    def view(self) -> QObject:
        found = self.root.findChild(QObject, "view")
        assert found is not None
        return found

    def lifecycle(self) -> int:
        return int(self.root.property("lifecycle"))

    def hide(self) -> None:
        self.view.setProperty("visible", False)

    def show(self) -> None:
        self.view.setProperty("visible", True)

    def run(self, code: str) -> None:
        QMetaObject.invokeMethod(self.view, "runJavaScript", Q_ARG(str, code))


@pytest.fixture
def loaded_scene(
    kondor_engine: QQmlEngine, qtbot: QtBot
) -> Iterator[tuple[Scene, Tab, PageServer]]:
    server = PageServer({"/": FORM_PAGE})
    tab = Tab(ProfileManager.instance().defaultProfile())
    scene = Scene(kondor_engine, tab)
    scene.view.setProperty("url", server.url())
    qtbot.waitUntil(lambda: bool(scene.root.property("loaded")), timeout=LOAD_TIMEOUT)
    yield scene, tab, server
    scene.window.close()
    scene.root.deleteLater()
    tab.deleteLater()


def test_hidden_idle_page_is_discarded(
    loaded_scene: tuple[Scene, Tab, PageServer], qtbot: QtBot
) -> None:
    scene, tab, _ = loaded_scene
    scene.hide()
    tab.sleep.requestIdleSleep()
    qtbot.waitUntil(lambda: scene.lifecycle() == DISCARDED, timeout=LOAD_TIMEOUT)
    assert tab.sleep.sleeping


def test_page_with_an_edited_field_is_not_discarded(
    loaded_scene: tuple[Scene, Tab, PageServer], qtbot: QtBot
) -> None:
    scene, tab, _ = loaded_scene
    scene.run("document.getElementById('q').value = 'typed'")
    scene.hide()
    tab.sleep.requestIdleSleep()
    qtbot.wait(SETTLE_MILLISECONDS)
    assert scene.lifecycle() != DISCARDED
    assert not tab.sleep.sleeping


def test_showing_the_view_wakes_the_page_with_the_same_url(
    loaded_scene: tuple[Scene, Tab, PageServer], qtbot: QtBot
) -> None:
    scene, tab, server = loaded_scene
    scene.hide()
    tab.sleep.putToSleep()
    qtbot.waitUntil(lambda: scene.lifecycle() == DISCARDED, timeout=LOAD_TIMEOUT)
    scene.show()
    qtbot.waitUntil(lambda: scene.lifecycle() == ACTIVE, timeout=LOAD_TIMEOUT)
    assert not tab.sleep.sleeping
    assert scene.view.property("url") == QUrl(server.url())
