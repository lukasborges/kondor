import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.tabs.tab import Tab
from kondor.extensions.extensionmanager import ExtensionManager
from tests.extensions.extensionsharness import allow_in_private_windows, install_sample
from tests.extensions.panel.panelfixture import PanelFixture
from tests.extensions.panel.panelitems import accessible_name_of, click_center_of, keep_alive
from tests.extensions.panel.test_pinnedtoolbar import (  # noqa: F401
    SAMPLE,
    ToolBar,
    accessibility,
    toolbar,
)

pytestmark = pytest.mark.no_qt_log


def manager() -> ExtensionManager:
    return ExtensionManager.instance()


def row_pin(panel: PanelFixture) -> QQuickItem:
    panel.wait_for(lambda: panel.row_at(0))
    pins = panel.finder.named(panel.row_at(0), "rowPinButton")
    assert len(pins) == 1
    keep_alive(pins[0])
    return pins[0]


def menu_of(button: QQuickItem) -> QObject:
    return button.findChild(QObject, "unpinMenu")


def right_click(button: QQuickItem) -> None:
    point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
    QTest.mouseClick(
        button.window(), Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, point
    )


def press_on(button: QQuickItem, key: Qt.Key, modifier: Qt.KeyboardModifier) -> None:
    button.forceActiveFocus()
    QTest.keyClick(button.window(), key, modifier)


def show_pinned(tool_bar: ToolBar) -> QQuickItem:
    tool_bar.show()
    tool_bar.pin()
    return tool_bar.wait_for_pinned_button()


def test_row_pin_toggles_pin(panel: PanelFixture) -> None:
    panel.open_panel()
    pin = row_pin(panel)
    click_center_of(pin)
    assert manager().isPinned(SAMPLE)
    assert panel.panel.property("opened")
    assert panel.current_id() == ""
    click_center_of(pin)
    assert not manager().isPinned(SAMPLE)


def test_shift_tab_from_row_pin_returns_to_row(panel: PanelFixture) -> None:
    panel.open_panel()
    pin = row_pin(panel)
    press_on(pin, Qt.Key.Key_Backtab, Qt.KeyboardModifier.ShiftModifier)
    assert panel.row_at(0).property("activeFocus")


def test_row_pin_is_checked_when_pinned(panel: PanelFixture) -> None:
    panel.open_panel()
    button = row_pin(panel)
    click_center_of(button)
    manager().setPinned(SAMPLE, False)
    panel.wait_for(lambda: not button.property("checked"))
    manager().setPinned(SAMPLE, True)
    panel.wait_for(lambda: button.property("checked"))
    manager().setPinned(SAMPLE, False)


def test_row_pin_names_the_extension(panel: PanelFixture) -> None:
    panel.open_panel()
    button = row_pin(panel)
    assert accessible_name_of(button) == "Pin Sample Extension to Toolbar"
    click_center_of(button)
    panel.wait_for(lambda: accessible_name_of(button) == "Unpin Sample Extension from Toolbar")
    manager().setPinned(SAMPLE, False)


def test_private_tab_has_no_row_pin(panel: PanelFixture) -> None:
    assert install_sample(panel.work)
    allow_in_private_windows(SAMPLE)
    panel.make_tab(Tab(QQuickWebEngineProfile()))
    panel.open_panel()
    assert not row_pin(panel).isVisible()


def test_level_two_has_no_pin_button(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    assert panel.finder.named(panel.item("backButton").parentItem().parentItem(), "pinButton") == []


def test_pinned_button_menu_unpins(toolbar: ToolBar) -> None:  # noqa: F811
    button = show_pinned(toolbar)
    right_click(button)
    menu = menu_of(button)
    toolbar.qtbot.waitUntil(lambda: menu.property("visible"))
    item = menu.findChild(QObject, "unpinMenuItem")
    click_center_of(item)
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is None)
    assert not manager().isPinned(SAMPLE)


@pytest.mark.parametrize(
    ("key", "modifier"),
    [
        (Qt.Key.Key_Menu, Qt.KeyboardModifier.NoModifier),
        (Qt.Key.Key_F10, Qt.KeyboardModifier.ShiftModifier),
    ],
)
def test_pinned_button_menu_opens_with_keys(
    toolbar: ToolBar,  # noqa: F811
    key: Qt.Key,
    modifier: Qt.KeyboardModifier,
) -> None:
    button = show_pinned(toolbar)
    press_on(button, key, modifier)
    menu = menu_of(button)
    toolbar.qtbot.waitUntil(lambda: menu.property("visible"))


def test_pinned_button_menu_from_keyboard_unpins_on_enter(toolbar: ToolBar) -> None:  # noqa: F811
    button = show_pinned(toolbar)
    press_on(button, Qt.Key.Key_F10, Qt.KeyboardModifier.ShiftModifier)
    menu = menu_of(button)
    toolbar.qtbot.waitUntil(lambda: menu.property("visible"))
    QTest.keyClick(button.window(), Qt.Key.Key_Return)
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is None)
    assert not manager().isPinned(SAMPLE)


def test_pinned_button_menu_from_right_click_has_no_current_item(toolbar: ToolBar) -> None:  # noqa: F811
    button = show_pinned(toolbar)
    right_click(button)
    menu = menu_of(button)
    toolbar.qtbot.waitUntil(lambda: menu.property("visible"))
    assert menu.property("currentIndex") == -1


def test_private_window_pinned_button_has_no_menu(toolbar: ToolBar) -> None:  # noqa: F811
    assert install_sample(toolbar.work)
    allow_in_private_windows(SAMPLE)
    show_pinned(toolbar)
    toolbar.tabs.addTab(True, QUrl("https://www.example.com/page"))
    button = toolbar.wait_for_pinned_button()
    right_click(button)
    press_on(button, Qt.Key.Key_Menu, Qt.KeyboardModifier.NoModifier)
    toolbar.qtbot.wait(200)
    assert not menu_of(button).property("visible")
