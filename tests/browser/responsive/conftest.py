from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

LOAD_TIMEOUT = 30000
SIZE = 900
PAGE_URL = "data:text/html,<title>page</title>hello"
SCENE_QML = """
import QtQuick
import Kondor

Item {
    id: scene
    width: 900
    height: 900
    property string devToolsUrl: ""
    property string consoleLog: ""
    property var devToolsView: null
    function find(item, name) {
        if (item.objectName === name)
            return item
        for (const child of item.children) {
            const found = find(child, name)
            if (found)
                return found
        }
        return null
    }
    function probe(source) {
        if (devToolsView)
            devToolsView.runJavaScript(source)
    }
    function sendConsoleMessage(message) {
        devToolsView.javaScriptConsoleMessage(0, message, 0, "")
    }
    property bool hasDevToolsFocus: false
    function ownsFocus() {
        let item = Window.window ? Window.window.activeFocusItem : null
        while (item && item !== devToolsView)
            item = item.parent
        return item !== null
    }
    Connections {
        target: scene.devToolsView
        function onJavaScriptConsoleMessage(level, message) {
            scene.consoleLog += message + "\\n"
        }
    }
    Timer {
        interval: 200; repeat: true; running: true
        onTriggered: {
            scene.devToolsView = scene.find(scene, "devTools")
            const view = scene.devToolsView
            scene.hasDevToolsFocus = scene.ownsFocus()
            scene.devToolsUrl = view && !view.loading ? view.url.toString() : ""
        }
    }
    Repeater {
        model: testTabModel
        delegate: WebViewTab {
            width: 900
            height: 900
            tabModel: testTabModel
            browserActions: ({})
        }
    }
}
"""


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
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
    quick_window.setProperty("scene", item)
    quick_window.show()
    yield quick_window
    quick_window.close()
    item.deleteLater()


@pytest.fixture
def tab_with_dev_tools(model: TabModel, window: QQuickWindow, qtbot: QtBot) -> Tab:
    tab: Tab = model.addTab()
    tab.navigateTo(QUrl(PAGE_URL))
    qtbot.waitUntil(lambda: tab.title == "page", timeout=LOAD_TIMEOUT)
    tab.toggleDevTools()
    qtbot.waitUntil(lambda: scene_url(window).startswith("devtools:"), timeout=LOAD_TIMEOUT)
    return tab


def scene_url(window: QQuickWindow) -> str:
    return str(window.property("scene").property("devToolsUrl"))


def console_log(window: QQuickWindow) -> str:
    return str(window.property("scene").property("consoleLog"))


def call_scene(window: QQuickWindow, method: str, argument: str) -> None:
    QMetaObject.invokeMethod(
        window.property("scene"),
        method,
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", argument),
    )
