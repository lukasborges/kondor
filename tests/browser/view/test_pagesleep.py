from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.extensions.pageserver import PageServer
from tests.qmlsupport import error_text, load_component, release

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


TAB_QML = """
import QtQuick
import Kondor

Item {
    id: holder
    width: 400; height: 300
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
    function hidePage() { findPageView(holder).visible = false }
    function lifecycle() { return findPageView(holder).lifecycleState }
    WebViewTab {
        anchors.fill: parent
        tab: testTab
        tabModel: testModel
        browserActions: null
    }
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

    def release(self, *owned: QObject) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)
        release(*owned)


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
    scene.release(tab, server)


def test_hidden_idle_page_is_discarded(
    loaded_scene: tuple[Scene, Tab, PageServer], qtbot: QtBot
) -> None:
    scene, tab, _ = loaded_scene
    scene.hide()
    tab.sleep.requestIdleSleep()
    qtbot.waitUntil(lambda: scene.lifecycle() == DISCARDED, timeout=LOAD_TIMEOUT)
    assert tab.sleep.sleeping


def lifecycle_of(holder: QObject) -> int:
    result = QMetaObject.invokeMethod(holder, "lifecycle", Q_RETURN_ARG("QVariant"))
    return int(result)


def test_sleeping_keeps_the_title_and_url_of_the_tab(
    kondor_engine: QQmlEngine, qtbot: QtBot
) -> None:
    server = PageServer({"/": FORM_PAGE})
    model = TabModel()
    tab = model.addTab()
    assert tab is not None
    kondor_engine.rootContext().setContextProperty("testTab", tab)
    kondor_engine.rootContext().setContextProperty("testModel", model)
    component = load_component(kondor_engine, TAB_QML)
    root = component.create()
    assert root is not None, error_text(component)
    tab.navigateTo(QUrl(server.url()))
    qtbot.waitUntil(lambda: tab.title == "form", timeout=LOAD_TIMEOUT)
    QMetaObject.invokeMethod(root, "hidePage")
    tab.sleep.putToSleep()
    qtbot.waitUntil(lambda: lifecycle_of(root) == DISCARDED, timeout=LOAD_TIMEOUT)
    assert (tab.title, tab.url.toString()) == ("form", server.url())
    release(root)
    release(component, model, server)


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
