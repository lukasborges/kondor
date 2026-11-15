import pytest

from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

PINNED_TABS = 2


def test_pinning_moves_tab_to_end_of_pinned_group(model: TabModel) -> None:
    first, second, third = model.addTab(), model.addTab(), model.addTab()
    model.setPinned(0, True)
    model.setPinned(2, True)
    assert model.pinnedCount == PINNED_TABS
    assert [model.indexOfTab(tab) for tab in (first, third, second)] == [0, 1, 2]


def test_unpinning_moves_tab_to_start_of_unpinned_tabs(model: TabModel) -> None:
    first, second, third = model.addTab(), model.addTab(), model.addTab()
    model.setPinned(0, True)
    model.setPinned(1, True)
    model.setPinned(0, False)
    assert model.pinnedCount == 1
    assert [model.indexOfTab(tab) for tab in (second, first, third)] == [0, 1, 2]


def test_move_tab_keeps_the_current_tab_selected(model: TabModel) -> None:
    model.addTab()
    second = model.addTab()
    model.addTab()
    model.setCurrentIndex(1)
    model.moveTab(0, 2)
    assert model.currentTab is second
    assert model.currentIndex == 0
