import pytest
from PySide6.QtGui import QAccessible, QAccessibleInterface

from pytests.browser.tabstrip.tabstripharness import TabStripHarness

pytestmark = pytest.mark.no_qt_log

MANY_TABS = 20


def is_visible_button(interface: QAccessibleInterface) -> bool:
    return not interface.state().invisible and interface.role() == QAccessible.Role.Button


def visible_buttons(interface: QAccessibleInterface) -> list[QAccessibleInterface]:
    found = [interface] if is_visible_button(interface) else []
    for index in range(interface.childCount()):
        found += visible_buttons(interface.child(index))
    return found


def has_no_name(interface: QAccessibleInterface) -> bool:
    return not interface.text(QAccessible.Text.Name)


def test_every_visible_button_has_a_name(strip: TabStripHarness) -> None:
    QAccessible.setActive(True)
    strip.add_tabs(MANY_TABS)
    assert strip.button_property("scrollLeftButton", "visible")
    root = QAccessible.queryAccessibleInterface(strip.window)
    buttons = visible_buttons(root)
    assert buttons
    assert [button for button in buttons if has_no_name(button)] == []
