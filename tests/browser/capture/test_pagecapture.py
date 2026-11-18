from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

PAGE_HEIGHT = 3000
VIEW_HEIGHT = 300
SCENE_QML = f"""
import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Item {{
    width: 400; height: 300
    property bool isLoading: view.loading
    property real viewHeight: view.height
    SplitView {{
        anchors.fill: parent
        orientation: Qt.Vertical
        WebEngineView {{
            id: view
            SplitView.fillHeight: true
            profile: testProfile
            url: "data:text/html,<body style='margin:0'><div style='height:{PAGE_HEIGHT}px'></div>"
        }}
    }}
    PageCapture {{ tab: testTab; webView: view }}
}}
"""


class Scene:
    def __init__(self, engine: QQmlEngine, tab: Tab) -> None:
        engine.rootContext().setContextProperty("testProfile", tab.profile)
        engine.rootContext().setContextProperty("testTab", tab)
        self.component: QQmlComponent = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.window.resize(400, VIEW_HEIGHT)
        self.root.setParentItem(self.window.contentItem())
        self.window.show()

    def release(self) -> None:
        self.window.close()
        release(self.root)
        release(self.window, self.component)


@pytest.fixture
def tab(kondor_engine: QQmlEngine) -> Iterator[Tab]:
    created = Tab(ProfileManager.instance().defaultProfile())
    yield created


@pytest.fixture
def scene(kondor_engine: QQmlEngine, tab: Tab, qtbot: QtBot) -> Iterator[Scene]:
    created = Scene(kondor_engine, tab)
    qtbot.waitUntil(lambda: not created.root.property("isLoading"), timeout=10000)
    qtbot.wait(500)
    yield created
    created.release()


def capture(tab: Tab, qtbot: QtBot, full_page: bool) -> QObject:
    with qtbot.waitSignal(tab.screenshotCaptured, timeout=10000) as blocker:
        tab.captureScreenshot(full_page)
    return blocker.args[0]


def test_visible_area_has_the_size_of_the_view(scene: Scene, tab: Tab, qtbot: QtBot) -> None:
    image = capture(tab, qtbot, False).property("image")
    assert (image.width(), image.height()) == (400, VIEW_HEIGHT)


def test_full_page_has_the_height_of_the_document(scene: Scene, tab: Tab, qtbot: QtBot) -> None:
    image = capture(tab, qtbot, True).property("image")
    assert image.height() == PAGE_HEIGHT


def test_full_page_gives_the_view_its_height_back(scene: Scene, tab: Tab, qtbot: QtBot) -> None:
    capture(tab, qtbot, True)
    qtbot.waitUntil(lambda: scene.root.property("viewHeight") == VIEW_HEIGHT, timeout=3000)
