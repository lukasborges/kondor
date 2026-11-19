import pytest
from PySide6.QtQuick import QQuickWindow

from kondor.browser.tabs.tab import Tab
from tests.browser.responsive.conftest import call_scene

pytestmark = pytest.mark.no_qt_log
ROUTING_MESSAGE = "kondor:toggle-responsive-mode"


def test_routing_message_toggles_responsive_mode(
    tab_with_dev_tools: Tab, window: QQuickWindow
) -> None:
    call_scene(window, "sendConsoleMessage", ROUTING_MESSAGE)
    assert tab_with_dev_tools.responsive.isActive

    call_scene(window, "sendConsoleMessage", ROUTING_MESSAGE)
    assert not tab_with_dev_tools.responsive.isActive


def test_other_console_messages_leave_responsive_mode_alone(
    tab_with_dev_tools: Tab, window: QQuickWindow
) -> None:
    call_scene(window, "sendConsoleMessage", "something else")
    assert not tab_with_dev_tools.responsive.isActive
