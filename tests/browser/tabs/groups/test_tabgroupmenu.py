import pytest
from PySide6.QtQml import QQmlEngine

from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

MENU_QML = """
import QtQuick
import Kondor
TabGroupMenu {
    tab: testTab
    tabIndex: 0
    tabModel: testModel
}
"""
EDITOR_QML = """
import QtQuick
import Kondor
TabGroupEditor {
    tabModel: testModel
    group: testGroup
}
"""
GROUP_ITEMS = 3
KEPT_COMPONENTS: list[object] = []


def create(engine: QQmlEngine, source: str, **context: object):
    for name, value in context.items():
        engine.rootContext().setContextProperty(name, value)
    component = load_component(engine, source)
    created = component.create()
    KEPT_COMPONENTS.append(component)
    assert created is not None, error_text(component)
    return created


def test_menu_offers_adding_an_ungrouped_tab(model: TabModel, kondor_engine: QQmlEngine) -> None:
    tab = model.addTab()
    menu = create(kondor_engine, MENU_QML, testTab=tab, testModel=model)
    assert menu.property("title") == "Add Tab to Group"


def test_menu_lists_other_groups_for_a_grouped_tab(
    model: TabModel, kondor_engine: QQmlEngine
) -> None:
    tab = model.addTab()
    model.addTab()
    model.newGroupForTab(0)
    model.newGroupForTab(1)
    menu = create(kondor_engine, MENU_QML, testTab=tab, testModel=model)
    assert menu.property("title") == "Move Tab to Group"
    assert menu.property("count") == GROUP_ITEMS


def test_editor_loads_for_a_group(model: TabModel, kondor_engine: QQmlEngine) -> None:
    model.addTab()
    group = model.newGroupForTab(0)
    editor = create(kondor_engine, EDITOR_QML, testModel=model, testGroup=group)
    assert editor.property("isCollapsed") is False
