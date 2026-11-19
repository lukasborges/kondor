import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.exceptions import TimeoutError as WaitTimeout
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from tests.browser.responsive.conftest import SIZE, call_scene, console_log

pytestmark = pytest.mark.no_qt_log
ROUTING_MESSAGE = "kondor:toggle-responsive-mode"
MESSAGE_LOGGED = (ROUTING_MESSAGE, "routing script did not log the message")
BUTTON_CLICKED = ("kondor-test:clicked", "device button not found")
READY_TIMEOUT = 20000
STEP_TIMEOUT = 5000
FIND_DEVICE_BUTTON = """
const walk = (root) => {
    for (const element of root.querySelectorAll('*')) {
        const previous = element.previousElementSibling;
        const previousLog = previous ? previous.getAttribute('jslog') || '' : '';
        const isNextToInspect = previousLog.includes('toggle-element-search');
        if (element.localName === 'devtools-button' && isNextToInspect)
            return element;
        const found = element.shadowRoot && walk(element.shadowRoot);
        if (found) return found;
    }
    return null;
};
const button = walk(document);
"""
REPORT_DEVICE_BUTTON = (
    "(() => { " + FIND_DEVICE_BUTTON + " if (button) console.log('kondor-test:button-found'); })()"
)
CLICK_DEVICE_BUTTON = (
    "(() => { "
    + FIND_DEVICE_BUTTON
    + " if (!button) return console.log('kondor-test:button-missing');"
    + " console.log('kondor-test:clicked'); button.click(); })()"
)


def wait_for_log(window: QQuickWindow, qtbot: QtBot, step: tuple[str, str]) -> None:
    text, failure = step
    try:
        qtbot.waitUntil(lambda: text in console_log(window), timeout=STEP_TIMEOUT)
    except WaitTimeout:
        pytest.fail(failure)


@pytest.fixture
def dev_tools_ready(tab_with_dev_tools: Tab, window: QQuickWindow, qtbot: QtBot) -> Tab:
    def report_button() -> bool:
        call_scene(window, "probe", REPORT_DEVICE_BUTTON)
        return "kondor-test:button-found" in console_log(window)

    try:
        qtbot.waitUntil(report_button, timeout=READY_TIMEOUT)
    except WaitTimeout:
        pytest.skip(
            "Developer Tools never built its device toolbar button, "
            "or never ran the page script (console log stayed empty)"
        )
    return tab_with_dev_tools


def focus_dev_tools(window: QQuickWindow, qtbot: QtBot) -> None:
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(SIZE // 2, SIZE - 50))
    try:
        qtbot.waitUntil(lambda: has_dev_tools_focus(window), timeout=STEP_TIMEOUT)
    except WaitTimeout:
        pytest.fail("Developer Tools never got the keyboard focus")


def has_dev_tools_focus(window: QQuickWindow) -> bool:
    return bool(window.property("scene").property("hasDevToolsFocus"))


def test_shortcut_in_dev_tools_toggles_responsive_mode(
    dev_tools_ready: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    focus_dev_tools(window, qtbot)
    modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.keyClick(window, Qt.Key.Key_M, modifiers)

    wait_for_log(window, qtbot, MESSAGE_LOGGED)
    assert dev_tools_ready.responsive.isActive, "message logged but tab.responsive did not turn on"


def test_device_button_in_dev_tools_toggles_responsive_mode(
    dev_tools_ready: Tab, window: QQuickWindow, qtbot: QtBot
) -> None:
    call_scene(window, "probe", CLICK_DEVICE_BUTTON)

    wait_for_log(window, qtbot, BUTTON_CLICKED)
    wait_for_log(window, qtbot, MESSAGE_LOGGED)
    assert dev_tools_ready.responsive.isActive, "message logged but tab.responsive did not turn on"
