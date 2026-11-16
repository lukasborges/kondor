from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    width: 200; height: 200
    WebEngineView { id: view; objectName: "view"; anchors.fill: parent; profile: testTab.profile }
    PageAudio { tab: testTab; webView: view }
}
"""


class Scene:
    def __init__(self, engine: QQmlEngine, tab: Tab) -> None:
        engine.rootContext().setContextProperty("testTab", tab)
        self.component = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.root.setParentItem(self.window.contentItem())

    @property
    def view(self) -> QObject:
        found = self.root.findChild(QObject, "view")
        assert found is not None
        return found


@pytest.fixture
def scene_and_tab(kondor_engine: QQmlEngine) -> Iterator[tuple[Scene, Tab]]:
    tab = Tab(ProfileManager.instance().defaultProfile())
    scene = Scene(kondor_engine, tab)
    yield scene, tab
    scene.root.deleteLater()
    tab.deleteLater()


def test_toggle_request_mutes_the_view_and_flows_back(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    scene, tab = scene_and_tab
    tab.audio.toggleMuted()
    qtbot.waitUntil(lambda: tab.audio.isMuted, timeout=2000)
    assert scene.view.property("audioMuted") is True


def test_second_toggle_request_unmutes_the_view(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    _, tab = scene_and_tab
    tab.audio.toggleMuted()
    qtbot.waitUntil(lambda: tab.audio.isMuted, timeout=2000)
    tab.audio.toggleMuted()
    qtbot.waitUntil(lambda: not tab.audio.isMuted, timeout=2000)


def test_new_view_starts_muted_when_the_tab_is_muted(
    kondor_engine: QQmlEngine,
) -> None:
    tab = Tab(ProfileManager.instance().defaultProfile())
    tab.audio.setMuted(True)
    scene = Scene(kondor_engine, tab)
    assert scene.view.property("audioMuted") is True
    scene.root.deleteLater()
    tab.deleteLater()
