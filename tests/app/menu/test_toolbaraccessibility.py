from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.menu.mainmenuharness import MainMenuHarness
from tests.app.menu.mainmenustub import TOOL_BAR_WINDOW_QML
from tests.qmlsupport import unnamed_buttons

pytestmark = pytest.mark.no_qt_log


@pytest.fixture
def tool_bar(menu_engine: QQmlEngine) -> Iterator[MainMenuHarness]:
    harness = MainMenuHarness(menu_engine, TOOL_BAR_WINDOW_QML)
    harness.tabs.addTab(False, QUrl("https://a.example"))
    harness.window.show()
    yield harness
    harness.close()


@pytest.mark.usefixtures("accessibility")
def test_every_visible_tool_bar_button_has_a_name(tool_bar: MainMenuHarness) -> None:
    assert QTest.qWaitForWindowExposed(tool_bar.window)

    content: QQuickItem = tool_bar.window.contentItem()
    assert unnamed_buttons(content) == []
