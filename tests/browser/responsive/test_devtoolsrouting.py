import contextlib
import os
from collections.abc import Callable, Iterator

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.exceptions import TimeoutError as WaitTimeout
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

pytestmark = [
    pytest.mark.no_qt_log,
    pytest.mark.skipif(
        bool(os.environ.get("CI")), reason="the DevTools frontend does not respond on CI runners"
    ),
]
LOAD_TIMEOUT = 30000
SIZE = 900
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
    function probe(source) {
        const view = find(this, "devTools")
        if (view)
            view.runJavaScript(source)
    }
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
FIND_DEVICE_BUTTON = """
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
"""
CLICK_DEVICE_BUTTON_ONCE = (
    "(() => { "
    + FIND_DEVICE_BUTTON
    + " if (!button || window.kondorClicked) return;"
    + " window.kondorClicked = true; button.click(); })()"
)
ATTEMPT_MS = 3000
ATTEMPTS = 8
NOT_ACTIVE = "responsive mode did not turn on: DevTools never took the action"


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


def run_in_dev_tools(window: QQuickWindow, source: str) -> None:
    QMetaObject.invokeMethod(
        window.property("scene"),
        "probe",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", source),
    )


def retry_until_active(tab: Tab, qtbot: QtBot, attempt: Callable[[], None]) -> None:
    for _ in range(ATTEMPTS):
        attempt()
        with contextlib.suppress(WaitTimeout):
            qtbot.waitUntil(lambda: tab.responsive.isActive, timeout=ATTEMPT_MS)
            return
    pytest.fail(NOT_ACTIVE)


def scene_url(window: QQuickWindow) -> str:
    return str(window.property("scene").property("devToolsUrl"))


def test_shortcut_in_dev_tools_toggles_responsive_mode(
    tab_with_dev_tools: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

    def press_shortcut_inside_dev_tools() -> None:
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(SIZE // 2, SIZE - 50))
        QTest.keyClick(window, Qt.Key.Key_M, modifiers)

    retry_until_active(tab_with_dev_tools, qtbot, press_shortcut_inside_dev_tools)


def test_device_button_in_dev_tools_toggles_responsive_mode(
    tab_with_dev_tools: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    def click_device_button() -> None:
        run_in_dev_tools(window, CLICK_DEVICE_BUTTON_ONCE)

    retry_until_active(tab_with_dev_tools, qtbot, click_device_button)
