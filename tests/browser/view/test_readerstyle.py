from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_RETURN_ARG, QMetaObject, QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

SCENE_QML = """
import QtQuick
import QtQuick.Window
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Window {
    visible: true

    function readerVars() { return readerStyle.readerVars() }

    Item {
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        id: viewItem
        function colors() {
            return [Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor,
                    Kirigami.Theme.linkColor, Kirigami.Theme.disabledTextColor].join("|")
        }
    }

    function expectedColors() { return viewItem.colors() }

    ReaderStyle {
        id: readerStyle
        tab: testTab
        webView: WebEngineView {}
        loadPending: false
    }
}
"""


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


def call(scene: QObject, name: str) -> object:
    return QMetaObject.invokeMethod(scene, name, Q_RETURN_ARG("QVariant"))


def load_scene(engine: QQmlEngine, model: TabModel) -> tuple[QQmlComponent, QObject]:
    engine.rootContext().setContextProperty("testTab", model.addTab())
    component = load_component(engine, SCENE_QML)
    scene = component.create()
    assert scene is not None, error_text(component)
    return component, scene


def test_builds_css_variables_from_the_view_theme_colors(
    model: TabModel, kondor_engine: QQmlEngine
) -> None:
    component, scene = load_scene(kondor_engine, model)
    variables = str(call(scene, "readerVars"))
    colors = str(call(scene, "expectedColors")).split("|")
    assert set(colors) != {"#000000"}
    for color in colors:
        assert color in variables
    del component
