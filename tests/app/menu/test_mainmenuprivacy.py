from collections.abc import Callable

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext

from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.app.remotecontrol.conftest import remote_control
from tests.qmlsupport import error_text, load_component

__all__ = ["remote_control"]
pytestmark = pytest.mark.no_qt_log
ACTIONS_QML = """
import QtQuick
import Kondor

BrowserActions {
    tabs: TabModel {}
    tabController: QtObject {}
    dialogs: QtObject {}
    fileDialogs: QtObject {}
    pageArea: QtObject {}
}
"""
PRIVATE_ACTIONS = ("newPrivateTabAction", "newPrivateWindowAction")


KEPT_COMPONENTS: list[QQmlComponent] = []


def is_enabled(engine: QQmlEngine, name: str) -> bool:
    component = load_component(engine, ACTIONS_QML)
    KEPT_COMPONENTS.append(component)
    actions = component.create()
    assert actions is not None, error_text(component)
    expression = QQmlExpression(qmlContext(actions), actions, f"{name}.enabled")
    value, _is_undefined = expression.evaluate()
    return bool(value)


@pytest.mark.parametrize("name", PRIVATE_ACTIONS)
def test_private_actions_are_enabled_by_default(kondor_engine: QQmlEngine, name: str) -> None:
    assert is_enabled(kondor_engine, name)


@pytest.mark.parametrize("name", PRIVATE_ACTIONS)
def test_private_actions_are_disabled_while_remote_control_is_on(
    kondor_engine: QQmlEngine, remote_control: RemoteControl, name: str
) -> None:
    remote_control.set_port(9333)

    assert not is_enabled(kondor_engine, name)


def test_normal_actions_stay_enabled_while_remote_control_is_on(
    kondor_engine: QQmlEngine, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)

    assert is_enabled(kondor_engine, "newTabAction")


TABS_ACTIONS_QML = ACTIONS_QML.replace("tabs: TabModel {}", "tabs: testTabs")


def screenshot_enabled_for(engine: QQmlEngine, tab_setup: Callable[[Tab], None]) -> bool:
    tabs = TabModel()
    tab = tabs.addTab()
    tab_setup(tab)
    engine.rootContext().setContextProperty("testTabs", tabs)
    component = load_component(engine, TABS_ACTIONS_QML)
    KEPT_COMPONENTS.append(component)
    actions = component.create()
    assert actions is not None, error_text(component)
    expression = QQmlExpression(qmlContext(actions), actions, "screenshotAction.enabled")
    KEPT_COMPONENTS.append(tabs)
    return bool(expression.evaluate()[0])


def test_screenshot_is_enabled_on_a_loaded_page(kondor_engine: QQmlEngine) -> None:
    assert screenshot_enabled_for(
        kondor_engine, lambda tab: tab.setUrl(QUrl("https://example.org/"))
    )


def test_screenshot_is_disabled_on_a_blank_page(kondor_engine: QQmlEngine) -> None:
    assert not screenshot_enabled_for(kondor_engine, lambda tab: tab.setUrl(QUrl("about:blank")))


def test_screenshot_is_disabled_on_a_certificate_error_page(kondor_engine: QQmlEngine) -> None:
    def show_error(tab: Tab) -> None:
        tab.setUrl(QUrl("https://expired.example/"))
        tab.security.setPendingCertificateError(QUrl("https://expired.example/"), "Expired", True)

    assert not screenshot_enabled_for(kondor_engine, show_error)
