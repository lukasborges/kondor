import pytest
from PySide6.QtCore import QUrl

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log


def test_starts_empty(model: TabModel) -> None:
    assert model.count == 0
    assert model.currentIndex == -1
    assert model.currentTab is None


def test_adds_and_activates_tabs(model: TabModel) -> None:
    model.addTab()
    assert (model.count, model.currentIndex) == (1, 0)
    model.addTab()
    model.addTab()
    assert (model.count, model.currentIndex) == (3, 2)
    assert model.currentTab is not None


def test_closing_current_middle_selects_next(model: TabModel) -> None:
    first, second, third = model.addTab(), model.addTab(), model.addTab()
    model.setCurrentIndex(1)
    assert model.currentTab is second
    model.closeTab(1)
    assert (model.count, model.currentIndex) == (2, 1)
    assert model.currentTab is third
    assert model.indexOfTab(first) == 0


def test_closing_current_last_selects_previous(model: TabModel) -> None:
    first = model.addTab()
    model.addTab()
    model.closeTab(1)
    assert (model.count, model.currentIndex) == (1, 0)
    assert model.currentTab is first


def test_closing_before_current_shifts_index(model: TabModel) -> None:
    first, second, third = model.addTab(), model.addTab(), model.addTab()
    model.setCurrentIndex(2)
    model.closeTab(0)
    assert (model.count, model.currentIndex) == (2, 1)
    assert model.currentTab is third
    assert model.indexOfTab(second) == 0
    assert model.indexOfTab(first) == -1


def test_closing_all_tabs_clears_current(model: TabModel) -> None:
    model.addTab()
    model.addTab()
    model.closeTab(0)
    model.closeTab(0)
    assert (model.count, model.currentIndex) == (0, -1)
    assert model.currentTab is None


def test_set_current_index_ignores_out_of_range(model: TabModel) -> None:
    model.addTab()
    model.addTab()
    model.setCurrentIndex(2)
    assert model.currentIndex == 1
    model.setCurrentIndex(-1)
    assert model.currentIndex == 1


def test_private_tab_uses_another_profile(model: TabModel) -> None:
    normal, private = model.addTab(False), model.addTab(True)
    assert not normal.isPrivate
    assert private.isPrivate
    assert private.profile.isOffTheRecord()
    assert private.profile is not normal.profile


def test_private_window_keeps_every_tab_private(model: TabModel) -> None:
    model.privateTabs = True
    from_add_tab = model.addTab(False)
    default_profile = ProfileManager.instance().defaultProfile()
    from_profile = model.addTabWithProfile(default_profile, QUrl("https://private.example"), False)
    assert from_add_tab.isPrivate
    assert from_profile.isPrivate
    assert from_profile.profile.isOffTheRecord()
