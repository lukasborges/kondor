from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    id: scene
    width: 400; height: 300
    property int hides: 0
    WebEngineView {
        id: view
        objectName: "view"
        anchors.fill: parent
        profile: testProfile
        onVisibleChanged: if (!visible) scene.hides++
    }
    PageRepaintOnRestore { webView: view }
}
"""


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

    def hides(self) -> int:
        return int(self.root.property("hides"))

    @property
    def view(self) -> QObject:
        found = self.root.findChild(QObject, "view")
        assert found is not None
        return found

    def hide_view(self) -> None:
        self.view.setProperty("visible", False)

    def release(self) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)


@pytest.fixture
def scene(kondor_engine: QQmlEngine) -> Iterator[Scene]:
    created = Scene(kondor_engine, ProfileManager.instance().defaultProfile())
    yield created
    created.release()


def test_restoring_from_minimized_toggles_the_visible_view(scene: Scene, qtbot: QtBot) -> None:
    scene.window.showMinimized()
    qtbot.wait(100)
    scene.window.showNormal()
    qtbot.waitUntil(lambda: scene.hides() == 1, timeout=3000)


def test_minimizing_alone_does_not_toggle_the_view(scene: Scene, qtbot: QtBot) -> None:
    scene.window.showMinimized()
    qtbot.wait(300)
    assert scene.hides() == 0


def test_restoring_leaves_a_hidden_view_hidden(scene: Scene, qtbot: QtBot) -> None:
    scene.hide_view()
    before = scene.hides()
    scene.window.showMinimized()
    qtbot.wait(100)
    scene.window.showNormal()
    qtbot.wait(300)
    assert scene.hides() == before
    assert not scene.view.property("visible")


def test_showing_without_minimizing_does_not_toggle_the_view(scene: Scene, qtbot: QtBot) -> None:
    scene.window.showMaximized()
    qtbot.wait(300)
    assert scene.hides() == 0
