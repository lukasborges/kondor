import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tabmodel import TabModel
from pytests.browser.tabs.conftest import site

pytestmark = pytest.mark.no_qt_log


def test_tabs_start_on_new_tab_page(model: TabModel) -> None:
    tab = model.addTab()
    assert tab.newTabPage
    assert tab.url.isEmpty()


def test_empty_navigation_does_nothing(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab()
    with qtbot.assertNotEmitted(tab.navigationRequested):
        tab.navigateTo(QUrl())
    assert tab.newTabPage


def test_navigate_leaves_new_tab_page(model: TabModel) -> None:
    tab = model.addTab()
    tab.navigateTo(site("a"))
    assert not tab.newTabPage


def test_show_new_tab_page_restores_it(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab(False, site("a"))
    assert not tab.newTabPage
    with qtbot.waitSignal(tab.newTabPageRequested, timeout=0):
        tab.showNewTabPage()
    assert tab.newTabPage


def test_about_blank_keeps_new_tab_page(model: TabModel) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("about:blank"))
    assert tab.newTabPage


def test_closed_new_tab_page_is_not_remembered(model: TabModel) -> None:
    model.addTab(False, site("a"))
    model.addTab()
    model.closeTab(1)
    assert not model.canReopenClosedTab
