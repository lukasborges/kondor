from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log
LOAD_TIMEOUT = 30000
SIZE = 900
SETTLE_MS = 1500
PAGE_URL = "data:text/html,<title>page</title>hello"
SCENE_QML = """
import QtQuick
import Kondor

Item {
    width: 900
    height: 900
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
    property string devToolsUrl: ""
    function runInDevTools(source) { find(this, "devTools").runJavaScript(source) }
    Timer {
        interval: 200; repeat: true; running: true
        onTriggered: {
            const view = parent.find(parent, "devTools")
            parent.devToolsUrl = view && !view.loading ? view.url.toString() : ""
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
CLICK_DEVICE_BUTTON = """
(() => {
    const walk = (root) => {
        for (const element of root.querySelectorAll('*')) {
            const previous = element.previousElementSibling;
            const previousLog = previous ? previous.getAttribute('jslog') || '' : '';
            const isNextToInspect = previousLog.includes('toggle-element-search');
            if (element.localName === 'devtools-button' && isNextToInspect)
                return element;
            const found = element.shadowRoot && walk(element.shadowRoot);
            if (found) return found;
        }
        return null;
    };
    const button = walk(document);
    if (button) button.click();
    return button !== null;
})()
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
    tab = model.addTab()
    tab.navigateTo(QUrl(PAGE_URL))
    qtbot.waitUntil(lambda: tab.title == "page", timeout=LOAD_TIMEOUT)
    tab.toggleDevTools()
    qtbot.waitUntil(lambda: scene_url(window).startswith("devtools:"), timeout=LOAD_TIMEOUT)
    qtbot.wait(SETTLE_MS)
    return tab


def scene_url(window: QQuickWindow) -> str:
    return str(window.property("scene").property("devToolsUrl"))


def test_shortcut_in_dev_tools_toggles_responsive_mode(
    tab_with_dev_tools: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(SIZE // 2, SIZE - 50))
    QTest.keyClick(window, Qt.Key.Key_M, modifiers)
    qtbot.waitUntil(lambda: tab_with_dev_tools.responsive.isActive, timeout=LOAD_TIMEOUT)


def test_device_button_in_dev_tools_toggles_responsive_mode(
    tab_with_dev_tools: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    scene = window.property("scene")
    QMetaObject.invokeMethod(
        scene,
        "runInDevTools",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", CLICK_DEVICE_BUTTON),
    )
    qtbot.waitUntil(lambda: tab_with_dev_tools.responsive.isActive, timeout=LOAD_TIMEOUT)
