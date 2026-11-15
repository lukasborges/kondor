from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from pytestqt.qtbot import QtBot

from tests.passwords.itemfinder import ItemFinder
from tests.passwords.panel.popupsupport import LOGINS, loaded_window, popup_qml


@pytest.fixture
def finder(kondor_engine: QQmlEngine) -> ItemFinder:
    return ItemFinder(kondor_engine)


@pytest.fixture
def popup_window(
    kondor_engine: QQmlEngine, finder: ItemFinder, qtbot: QtBot
) -> Iterator[QQuickWindow]:
    with loaded_window(kondor_engine, popup_qml(LOGINS)) as window:
        finder.open_popup(window)
        qtbot.waitUntil(lambda: finder.is_popup_opened(window))
        qtbot.waitUntil(finder.popup_items(window, "passwordSearchField")[0].hasActiveFocus)
        yield window
