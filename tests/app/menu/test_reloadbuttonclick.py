from collections.abc import Iterator

import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.menu.mainmenuharness import MainMenuHarness
from tests.app.menu.mainmenustub import TOOL_BAR_WINDOW_QML

pytestmark = [pytest.mark.no_qt_log, pytest.mark.usefixtures("accessibility")]

SHIFT = Qt.KeyboardModifier.ShiftModifier
NONE = Qt.KeyboardModifier.NoModifier


@pytest.fixture
def tool_bar(menu_engine: QQmlEngine) -> Iterator[MainMenuHarness]:
    harness = MainMenuHarness(menu_engine, TOOL_BAR_WINDOW_QML)
    harness.tabs.addTab(False, QUrl("https://a.example"))
    harness.window.show()
    assert QTest.qWaitForWindowExposed(harness.window)
    yield harness
    harness.close()


def is_named_button(item: QQuickItem, name: str) -> bool:
    if not item.inherits("QQuickAbstractButton"):
        return False
    accessible = QAccessible.queryAccessibleInterface(item)
    return accessible is not None and accessible.text(QAccessible.Text.Name) == name


def find_reload_button(item: QQuickItem) -> QQuickItem | None:
    if is_named_button(item, "Reload"):
        return item
    for child in item.childItems():
        found = find_reload_button(child)
        if found is not None:
            return found
    return None


def click_reload(harness: MainMenuHarness, modifiers: Qt.KeyboardModifier) -> list[str]:
    emitted: list[str] = []
    tab = harness.tabs.currentTab
    tab.reloadRequested.connect(lambda: emitted.append("normal"))
    tab.reloadBypassingCacheRequested.connect(lambda: emitted.append("bypass"))
    button = find_reload_button(harness.window.contentItem())
    assert button is not None
    center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
    QTest.mouseClick(harness.window, Qt.MouseButton.LeftButton, modifiers, center)
    return emitted


def test_shift_click_reloads_without_the_cache(tool_bar: MainMenuHarness) -> None:
    assert click_reload(tool_bar, SHIFT) == ["bypass"]


def test_plain_click_does_a_normal_reload(tool_bar: MainMenuHarness) -> None:
    assert click_reload(tool_bar, NONE) == ["normal"]
