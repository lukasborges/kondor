from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_RETURN_ARG, QMetaObject, QObject
from PySide6.QtQml import QQmlEngine

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

MENU_QML = """
import QtQuick
import Kondor
TabContextMenu { tab: testTab; tabModel: testModel }
"""


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


def can_put_to_sleep(engine: QQmlEngine, tab: Tab, model: TabModel) -> bool:
    engine.rootContext().setContextProperty("testTab", tab)
    engine.rootContext().setContextProperty("testModel", model)
    component = load_component(engine, MENU_QML)
    menu = component.create()
    assert menu is not None, error_text(component)
    result = QMetaObject.invokeMethod(menu, "canPutToSleep", Q_RETURN_ARG("QVariant"))
    assert isinstance(menu, QObject)
    return bool(result)


def two_tabs(model: TabModel) -> tuple[Tab, Tab]:
    background = model.addTab()
    current = model.addTab()
    assert background is not None and current is not None
    return background, current


def test_background_tab_can_be_put_to_sleep(model: TabModel, kondor_engine: QQmlEngine) -> None:
    background, _ = two_tabs(model)
    background.setUrl(background.url.fromUserInput("https://a.example"))
    assert can_put_to_sleep(kondor_engine, background, model)


def test_current_tab_cannot_be_put_to_sleep(model: TabModel, kondor_engine: QQmlEngine) -> None:
    _, current = two_tabs(model)
    current.setUrl(current.url.fromUserInput("https://a.example"))
    assert not can_put_to_sleep(kondor_engine, current, model)


def test_sleeping_tab_cannot_be_put_to_sleep(model: TabModel, kondor_engine: QQmlEngine) -> None:
    background, _ = two_tabs(model)
    background.setUrl(background.url.fromUserInput("https://a.example"))
    background.sleep.setSleeping(True)
    assert not can_put_to_sleep(kondor_engine, background, model)
