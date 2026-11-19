from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log
MESSAGE = "kondor:toggle-responsive-mode"
SCRIPT_PATH = Path(__file__).parents[3] / "src/kondor/browser/responsive/devtoolsrouting.js"
PAGE = (
    "data:text/html,<title>ready</title>"
    "<div jslog='toggle-element-search'></div><devtools-button id=b></devtools-button>"
    "<devtools-button id=other></devtools-button>"
)
SCENE_QML = """
import QtQuick
import QtWebEngine

Item {
    id: scene
    width: 400; height: 300
    property var messages: []
    property var results: []
    function run(source) {
        view.runJavaScript(source, function(result) {
            scene.results = scene.results.concat([result])
        })
    }
    WebEngineView {
        id: view
        objectName: "view"
        anchors.fill: parent
        profile: testProfile
        onJavaScriptConsoleMessage: function(level, message) {
            scene.messages = scene.messages.concat([message])
        }
    }
}
"""
KEY_EVENT = (
    "(() => {{ const event = new KeyboardEvent('keydown', {{ code: '{code}', ctrlKey: {ctrl},"
    " shiftKey: true, cancelable: true }}); document.body.dispatchEvent(event);"
    " return event.defaultPrevented; }})()"
)
CLICK_EVENT = (
    "(() => {{ const event = new MouseEvent('click', {{ bubbles: true, composed: true,"
    " cancelable: true }}); document.getElementById('{id}').dispatchEvent(event);"
    " return event.defaultPrevented; }})()"
)


class Scene:
    def __init__(self, engine: QQmlEngine, profile: QObject) -> None:
        engine.rootContext().setContextProperty("testProfile", profile)
        self.component: QQmlComponent = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.window.resize(400, 300)
        self.root.setParentItem(self.window.contentItem())
        self.window.show()

    def messages(self) -> list[str]:
        return list(self.root.property("messages").toVariant())

    def results(self) -> list[object]:
        return list(self.root.property("results").toVariant())

    def run(self, qtbot: QtBot, source: str) -> object:
        count = len(self.results())
        QMetaObject.invokeMethod(
            self.root, "run", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", source)
        )
        qtbot.waitUntil(lambda: len(self.results()) > count, timeout=15000)
        return self.results()[-1]

    def release(self) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)


@pytest.fixture
def scene(kondor_engine: QQmlEngine, qtbot: QtBot) -> Iterator[Scene]:
    created = Scene(kondor_engine, ProfileManager.instance().defaultProfile())
    view = created.root.findChild(QObject, "view")
    assert view is not None
    view.setProperty("url", QUrl(PAGE))
    qtbot.waitUntil(lambda: view.property("title") == "ready", timeout=30000)
    script = SCRIPT_PATH.read_text().replace('location.protocol === "devtools:"', "true")
    created.run(qtbot, script)
    yield created
    created.release()


def test_shortcut_is_redirected_and_stopped(scene: Scene, qtbot: QtBot) -> None:
    assert scene.run(qtbot, KEY_EVENT.format(code="KeyM", ctrl="true")) is True
    qtbot.waitUntil(lambda: MESSAGE in scene.messages(), timeout=5000)


def test_other_shortcuts_are_left_alone(scene: Scene, qtbot: QtBot) -> None:
    assert scene.run(qtbot, KEY_EVENT.format(code="KeyN", ctrl="true")) is False
    assert scene.run(qtbot, KEY_EVENT.format(code="KeyM", ctrl="false")) is False
    assert MESSAGE not in scene.messages()


def test_device_button_click_is_redirected_and_stopped(scene: Scene, qtbot: QtBot) -> None:
    assert scene.run(qtbot, CLICK_EVENT.format(id="b")) is True
    qtbot.waitUntil(lambda: MESSAGE in scene.messages(), timeout=5000)


def test_other_buttons_are_left_alone(scene: Scene, qtbot: QtBot) -> None:
    assert scene.run(qtbot, CLICK_EVENT.format(id="other")) is False
    assert MESSAGE not in scene.messages()
