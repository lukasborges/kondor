import pytest
from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.extensions.panel.panelfixture import PanelFixture

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"


def press(panel: PanelFixture, key: Qt.Key) -> None:
    QTest.keyClick(panel.window, key)


def first_row(panel: PanelFixture) -> QQuickItem:
    panel.wait_for(lambda: panel.row_at(0))
    return panel.row_at(0)


def test_list_opens_with_no_focused_row(panel: PanelFixture) -> None:
    panel.open_panel()
    assert not first_row(panel).hasActiveFocus()
    assert panel.item("panelExtensionList").property("currentIndex") == -1


def test_down_focuses_first_row(panel: PanelFixture) -> None:
    panel.open_panel()
    row = first_row(panel)
    press(panel, Qt.Key.Key_Down)
    panel.wait_for(row.hasActiveFocus)


def test_enter_right_after_opening_does_nothing(panel: PanelFixture) -> None:
    panel.open_panel()
    press(panel, Qt.Key.Key_Return)
    assert panel.current_id() == ""


def test_actions_open_with_no_focused_entry(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    assert panel.actions_root().hasActiveFocus()
    assert not panel.item("backButton").hasActiveFocus()


def test_down_focuses_first_action_entry(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    press(panel, Qt.Key.Key_Down)
    assert panel.window.activeFocusItem() is not panel.actions_root()


def test_enter_right_after_opening_actions_does_nothing(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    press(panel, Qt.Key.Key_Return)
    assert panel.current_id() == SAMPLE
