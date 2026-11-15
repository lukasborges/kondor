import pytest
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext

from kondor.app.remotecontrol.remotecontrol import RemoteControl
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
