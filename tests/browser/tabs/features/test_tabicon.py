import pytest
from PySide6.QtCore import QUrl

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

PAGE = QUrl("https://example.org/page")
ICON = QUrl("https://example.org/favicon.ico")


def tab_with_icon(model: TabModel) -> Tab:
    tab = model.addTab()
    tab.setUrl(PAGE)
    tab.setIconUrl(ICON)
    return tab


def test_download_on_another_origin_keeps_the_page_icon(model: TabModel) -> None:
    tab = tab_with_icon(model)
    tab.setUrl(QUrl("https://files.example.net/file.dat"))
    tab.setIconUrl(QUrl())
    tab.setUrl(PAGE)
    assert tab.iconUrl == ICON


def test_download_on_the_same_origin_keeps_the_page_icon(model: TabModel) -> None:
    tab = tab_with_icon(model)
    tab.setUrl(QUrl("https://example.org/file.dat"))
    tab.setIconUrl(QUrl())
    tab.setUrl(PAGE)
    assert tab.iconUrl == ICON


def test_successful_load_without_an_icon_clears_the_icon(model: TabModel) -> None:
    tab = tab_with_icon(model)
    tab.setUrl(QUrl("https://other.example.net/"))
    tab.settleIconUrl(QUrl())
    assert tab.iconUrl.isEmpty()


def test_successful_load_with_an_icon_keeps_it(model: TabModel) -> None:
    tab = tab_with_icon(model)
    tab.settleIconUrl(ICON)
    assert tab.iconUrl == ICON


def test_failed_load_without_an_icon_clears_the_icon(model: TabModel) -> None:
    tab = tab_with_icon(model)
    tab.setUrl(QUrl("http://127.0.0.1:1/"))
    tab.setIconUrl(QUrl())
    tab.settleIconUrl(QUrl())
    assert tab.iconUrl.isEmpty()
