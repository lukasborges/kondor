from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from kondor.site.sitesettings import SiteSettings
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

SCENE_QML = """
import QtQuick
import Kondor

Item {
    width: 600
    height: 100
    Item { id: field; objectName: "field"; anchors.fill: parent }
    PopupBlockedButton {
        objectName: "button"
        tabs: testTabs
        addressField: field
    }
}
"""
PAGE = "https://tickets.example.com/checkout"
POPUP = "https://payment.example.net/3ds?session=1"


class Scene:
    def __init__(self, engine: QQmlEngine, tabs: TabModel) -> None:
        engine.rootContext().setContextProperty("testTabs", tabs)
        self.component = load_component(engine, SCENE_QML)
        created = self.component.create()
        assert isinstance(created, QQuickItem), error_text(self.component)
        self.root = created
        self.window = QQuickWindow()
        self.root.setParentItem(self.window.contentItem())
        self.window.show()

    @property
    def button(self) -> QQuickItem:
        found = self.root.findChild(QQuickItem, "button")
        assert found is not None
        return found

    def release(self) -> None:
        self.window.close()
        release(self.root, self.window, self.component)


@pytest.fixture
def tabs(qapp: object, isolated_profile: object, site_settings: SiteSettings) -> Iterator[TabModel]:
    Settings.instance().setProperty("blockPopups", True)
    model = TabModel()
    yield model
    release(model)


@pytest.fixture
def scene(tabs: TabModel, kondor_engine: QQmlEngine) -> Iterator[Scene]:
    shown = Scene(kondor_engine, tabs)
    yield shown
    shown.release()


def open_tab(tabs: TabModel) -> Tab:
    tab = tabs.addTab()
    tab.setUrl(tab.url.fromUserInput(PAGE))
    return tab


def test_button_is_hidden_until_something_is_blocked(tabs: TabModel, scene: Scene) -> None:
    tab = open_tab(tabs)
    assert not scene.button.isVisible()
    tab.popups.add_blocked(POPUP)
    assert scene.button.isVisible()


def test_button_hides_again_after_the_last_pop_up_is_opened(tabs: TabModel, scene: Scene) -> None:
    tab = open_tab(tabs)
    tab.popups.add_blocked(POPUP)
    tab.popups.openBlocked(POPUP)
    assert not scene.button.isVisible()
