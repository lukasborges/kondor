import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.closedtabs import ClosedTabs
from kondor.browser.tabs.tabmodel import TabModel
from tests.browser.tabs.conftest import site

pytestmark = pytest.mark.no_qt_log
REMAINING_TABS = 2


def add_sites(model: TabModel, *names: str) -> None:
    for name in names:
        model.addTab(False, site(name))


def closed_urls(model: TabModel) -> list[QUrl]:
    return [entry["url"] for entry in model.recentlyClosed]


def test_reopen_closed_tab_restores_position(model: TabModel) -> None:
    add_sites(model, "a", "b", "c")
    assert not model.canReopenClosedTab
    model.closeTab(1)
    assert model.count == REMAINING_TABS
    assert model.canReopenClosedTab
    model.reopenClosedTab()
    assert (model.count, model.currentIndex) == (3, 1)
    assert model.currentTab.url == site("b")
    assert not model.canReopenClosedTab


def test_private_tabs_are_not_reopened(model: TabModel) -> None:
    add_sites(model, "a")
    model.addTab(True, site("private"))
    model.closeTab(1)
    assert model.count == 1
    assert not model.canReopenClosedTab
    model.reopenClosedTab()
    assert model.count == 1


def test_recently_closed_lists_newest_first(model: TabModel, qtbot: QtBot) -> None:
    add_sites(model, "a", "b", "c")
    assert model.recentlyClosed == []
    with qtbot.waitSignals([model.recentlyClosedChanged] * 2, timeout=0):
        model.closeTab(0)
        model.closeTab(1)
    assert closed_urls(model) == [site("c"), site("a")]


def test_reopen_closed_tab_by_index(model: TabModel) -> None:
    add_sites(model, "a", "b", "c")
    model.closeTab(0)
    model.closeTab(1)
    model.reopenClosedTab(1)
    assert model.currentTab.url == site("a")
    assert closed_urls(model) == [site("c")]
    model.reopenClosedTab(5)
    assert closed_urls(model) == [site("c")]


def test_private_tabs_are_not_in_recently_closed(model: TabModel) -> None:
    add_sites(model, "a")
    model.addTab(True, site("private"))
    model.closeTab(1)
    assert model.recentlyClosed == []


def test_recently_closed_keeps_at_most_the_limit(model: TabModel) -> None:
    add_sites(model, *(f"site{index}" for index in range(25)))
    for _ in range(25):
        model.closeTab(0)
    assert len(model.recentlyClosed) == ClosedTabs.MAX_CLOSED_TABS
    assert closed_urls(model)[0] == site("site24")
