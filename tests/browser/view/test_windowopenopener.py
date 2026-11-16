from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE
from tests.extensions.pageserver import PageServer
from tests.qmlsupport import error_text, load_component

LOAD_TIMEOUT = 30000
TABS_WITH_POPUP = 2
OPENER_PAGE = b"<html><head><title>opener</title></head><body>opener</body></html>"
POPUP_PAGE = b"""<html><head><title>t</title></head><body><script>
document.title = 'opener:' + (window.opener !== null);
</script></body></html>"""
SCENE_QML = """
import QtQuick
import Kondor

Item {
    width: 400
    height: 300
    Repeater {
        model: testTabModel
        delegate: WebViewTab {
            width: 400
            height: 300
            tabModel: testTabModel
            browserActions: ({})
        }
    }
}
"""
OPEN_POPUP = "window.open('/popup', '_blank');"


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


@pytest.fixture
def scene(model: TabModel, kondor_engine: QQmlEngine) -> Iterator[QQuickItem]:
    kondor_engine.rootContext().setContextProperty("testTabModel", model)
    component = load_component(kondor_engine, SCENE_QML)
    item = component.create()
    assert item is not None, error_text(component)
    window = QQuickWindow()
    item.setParentItem(window.contentItem())
    window.show()
    yield item
    window.close()
    item.deleteLater()


def find_item(item: QQuickItem, name: str) -> QQuickItem | None:
    if item.objectName() == name:
        return item
    found = (find_item(child, name) for child in item.childItems())
    return next((match for match in found if match is not None), None)


class Browser:
    def __init__(self, model: TabModel, scene: QQuickItem, qtbot: QtBot) -> None:
        self.model = model
        self.scene = scene
        self.qtbot = qtbot
        self.server = PageServer({"/": OPENER_PAGE, "/popup": POPUP_PAGE})

    def open_popup(self, private: bool) -> tuple[Tab, Tab]:
        opener = self.model.addTab(private)
        opener.navigateTo(self.server.url())
        self.qtbot.waitUntil(lambda: opener.title == "opener", timeout=LOAD_TIMEOUT)
        view = find_item(self.scene, "pageView")
        assert QMetaObject.invokeMethod(view, "runJavaScript", Q_ARG(str, OPEN_POPUP))
        self.qtbot.waitUntil(lambda: self.model.rowCount() == TABS_WITH_POPUP, timeout=LOAD_TIMEOUT)
        popup = self.model.data(self.model.index(1), TAB_ROLE)
        return opener, popup

    def wait_for_title(self, tab: Tab, title: str) -> None:
        self.qtbot.waitUntil(lambda: tab.title == title, timeout=LOAD_TIMEOUT)


@pytest.fixture
def browser(model: TabModel, scene: QQuickItem, qtbot: QtBot) -> Browser:
    return Browser(model, scene, qtbot)


def test_popup_keeps_the_window_opener(browser: Browser) -> None:
    _, popup = browser.open_popup(private=False)
    browser.wait_for_title(popup, "opener:true")


def test_popup_of_a_private_tab_uses_the_private_profile_of_the_opener(browser: Browser) -> None:
    opener, popup = browser.open_popup(private=True)
    assert popup.profile is opener.profile
    browser.wait_for_title(popup, "opener:true")
