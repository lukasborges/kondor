from collections.abc import Iterator

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from tests.browser.address.addressbarharness import AddressBarHarness, seed_history

pytestmark = pytest.mark.no_qt_log

MIN_ROWS = 3
THIRD_ROW = 2
SECOND_ROW = 1
SETTLE_MS = 400


@pytest.fixture
def harness(
    kondor_engine: QQmlEngine, desktop_style: None, qtbot: QtBot
) -> Iterator[AddressBarHarness]:
    seed_history()
    opened = AddressBarHarness(kondor_engine, qtbot)
    yield opened
    opened.close()


def completed_inline(harness: AddressBarHarness) -> bool:
    return harness.text() == "kde.org"


def test_completes_a_known_host_inline(harness: AddressBarHarness, qtbot: QtBot) -> None:
    harness.type("kd")
    qtbot.waitUntil(lambda: completed_inline(harness))
    assert harness.bar_property("selectedText") == "e.org"


def test_backspace_after_a_completion_does_not_complete_again(
    harness: AddressBarHarness, qtbot: QtBot
) -> None:
    harness.type("kd")
    qtbot.waitUntil(lambda: completed_inline(harness))
    harness.press(Qt.Key.Key_Backspace)
    QTest.qWait(SETTLE_MS)
    assert harness.text() == "kd"


def test_down_and_up_move_through_the_suggestions(harness: AddressBarHarness, qtbot: QtBot) -> None:
    harness.type("kd")
    qtbot.waitUntil(harness.is_open)
    qtbot.waitUntil(lambda: completed_inline(harness))
    assert harness.row_count() >= MIN_ROWS
    harness.press(Qt.Key.Key_Down)
    harness.press(Qt.Key.Key_Down)
    assert harness.suggestions_property("currentIndex") == THIRD_ROW
    assert harness.text() == harness.text_of_row(THIRD_ROW)
    harness.press(Qt.Key.Key_Up)
    assert harness.suggestions_property("currentIndex") == SECOND_ROW
    assert harness.text() == harness.text_of_row(SECOND_ROW)


def test_escape_restores_the_typed_text_and_closes_the_suggestions(
    harness: AddressBarHarness, qtbot: QtBot
) -> None:
    harness.type("kd")
    qtbot.waitUntil(harness.is_open)
    harness.press(Qt.Key.Key_Down)
    harness.press(Qt.Key.Key_Down)
    assert harness.text() != "kd"
    harness.press(Qt.Key.Key_Escape)
    assert harness.text() == "kd"
    assert not harness.is_open()


def test_enter_navigates_the_current_tab(harness: AddressBarHarness, qtbot: QtBot) -> None:
    with qtbot.waitSignal(harness.tabs.currentTab.navigationRequested, timeout=2000) as signal:
        harness.type("example.org")
        harness.press(Qt.Key.Key_Return)
    expected = ProfileManager.instance().resolveAddress("example.org")
    assert signal.args == [expected]


def test_switching_the_current_tab_shows_its_url(harness: AddressBarHarness, qtbot: QtBot) -> None:
    assert harness.text() == "https://kde.org/one"
    harness.tabs.addTab(False, QUrl("https://example.org/two"))
    qtbot.waitUntil(lambda: harness.text() == "https://example.org/two")
    harness.tabs.setCurrentIndex(0)
    qtbot.waitUntil(lambda: harness.text() == "https://kde.org/one")


def test_a_focused_address_bar_follows_the_current_tab(
    harness: AddressBarHarness, qtbot: QtBot
) -> None:
    harness.tabs.addTab(False, QUrl("https://example.com/two"))
    qtbot.waitUntil(lambda: harness.text() == "https://example.com/two")
    harness.call("focusBar")
    harness.tabs.setCurrentIndex(0)
    assert harness.text() == "https://kde.org/one"
