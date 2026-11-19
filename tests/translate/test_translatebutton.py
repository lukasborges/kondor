from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from kondor.translate.service import TranslationService
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

SCENE_QML = """
import QtQuick
import QtQuick.Layouts
import Kondor

Item {
    width: 600
    height: 100
    Item { id: field; anchors.fill: parent }
    RowLayout {
        anchors.fill: parent
        Item { Layout.fillWidth: true }
        TranslateButton { objectName: "button"; tabs: testTabs; addressField: field }
    }
}
"""


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
def tab(qapp: object, isolated_profile: object, monkeypatch: pytest.MonkeyPatch) -> Iterator[Tab]:
    Settings.instance().setProperty("translateTo", "pt")
    service = TranslationService.instance()
    monkeypatch.setattr(service, "ensure_catalog", lambda ready: ready(True))
    monkeypatch.setattr(service, "is_offered", lambda source, target: source in ("en", "de"))
    model = TabModel()
    yield model.addTab()
    release(model)


@pytest.fixture
def scene(tab: Tab, kondor_engine: QQmlEngine) -> Iterator[Scene]:
    shown = Scene(kondor_engine, tab.parent())
    yield shown
    shown.release()


def test_button_is_hidden_until_the_page_language_is_known(tab: Tab, scene: Scene) -> None:
    assert not scene.button.isVisible()
    tab.translation.receive_language("en-US", "")
    assert scene.button.isVisible()


def test_button_is_hidden_for_the_target_language(tab: Tab, scene: Scene) -> None:
    tab.translation.receive_language("pt-BR", "")
    assert not scene.button.isVisible()


def test_button_is_hidden_for_a_language_on_the_never_list(tab: Tab, scene: Scene) -> None:
    tab.translation.receive_language("de", "")
    tab.translation.lists.setNever(True)
    assert not scene.button.isVisible()
    tab.translation.lists.setNever(False)
    assert scene.button.isVisible()


def test_button_hides_when_the_page_starts_loading_again(tab: Tab, scene: Scene) -> None:
    tab.translation.receive_language("en", "")
    tab.setLoading(True)
    assert not scene.button.isVisible()
