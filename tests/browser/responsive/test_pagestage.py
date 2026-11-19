from collections.abc import Iterator
from urllib.parse import quote

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from tests.qmlsupport import error_text, load_component, release

MIN_FIT = 0.2
MAX_FIT = 0.5

pytestmark = pytest.mark.no_qt_log

PAGE = (
    "<title>x</title><script>function show() {"
    " document.title = innerWidth + 'x' + innerHeight + '@' + devicePixelRatio }"
    "; addEventListener('resize', show); show()</script>"
)
SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

PageStage {
    id: stage
    width: 1100; height: 700
    tab: testTab
    WebEngineView {
        id: view
        objectName: "view"
        anchors.fill: parent
        profile: testTab.profile
        zoomFactor: stage.pageZoom
        url: "data:text/html,PAGE_URL"
    }
}
""".replace("PAGE_URL", quote(PAGE))


class Scene:
    def __init__(self, engine: QQmlEngine, tab: Tab) -> None:
        engine.rootContext().setContextProperty("testTab", tab)
        self.component = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root: QQuickItem = created
        self.window = QQuickWindow()
        self.window.resize(1100, 700)
        self.root.setParentItem(self.window.contentItem())
        self.window.show()

    @property
    def view(self) -> QObject:
        found = self.root.findChild(QObject, "view")
        assert found is not None
        return found

    def release(self, *owned: QObject) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)
        release(*owned)


@pytest.fixture
def scene_and_tab(kondor_engine: QQmlEngine) -> Iterator[tuple[Scene, Tab]]:
    tab = Tab(ProfileManager.instance().defaultProfile())
    scene = Scene(kondor_engine, tab)
    yield scene, tab
    scene.release(tab)


def test_page_fills_the_area_when_the_mode_is_off(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    scene, _ = scene_and_tab
    qtbot.waitUntil(lambda: scene.view.property("title") == "1100x700@1", timeout=20000)


def test_page_lays_out_at_the_device_size(scene_and_tab: tuple[Scene, Tab], qtbot: QtBot) -> None:
    scene, tab = scene_and_tab
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("iphone-16")
    qtbot.waitUntil(lambda: scene.view.property("title") == "393x852@3", timeout=20000)


def test_large_device_is_scaled_down_to_fit_the_area(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    scene, tab = scene_and_tab
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("ipad-pro-13")
    qtbot.waitUntil(lambda: scene.view.property("title") == "1032x1376@2", timeout=20000)
    assert MIN_FIT < scene.root.property("fitScale") < MAX_FIT


def test_page_keeps_its_size_without_zoom_to_fit(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    scene, tab = scene_and_tab
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("ipad-pro-13")
    tab.responsive.setZoomToFit(False)
    assert scene.root.property("fitScale") == 1


def test_page_sees_the_device_pixel_ratio(scene_and_tab: tuple[Scene, Tab], qtbot: QtBot) -> None:
    scene, tab = scene_and_tab
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("pixel-9")
    qtbot.waitUntil(lambda: scene.view.property("title") == "412x924@2.625", timeout=20000)


def test_lowering_the_ratio_keeps_the_css_size(
    scene_and_tab: tuple[Scene, Tab], qtbot: QtBot
) -> None:
    scene, tab = scene_and_tab
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("pixel-9")
    tab.responsive.setRatio(1)
    qtbot.waitUntil(lambda: scene.view.property("title") == "412x924@1", timeout=20000)
