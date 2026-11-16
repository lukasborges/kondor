import pytest
from PySide6.QtCore import QUrl

from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

ICON = QUrl("https://example.org/favicon.ico")


def test_empty_icon_from_a_download_navigation_keeps_the_page_icon(model: TabModel) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("https://example.org/page"))
    tab.setIconUrl(ICON)
    tab.setIconUrl(QUrl())
    assert tab.iconUrl == ICON


def test_navigating_to_another_site_clears_the_icon(model: TabModel) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("https://example.org/page"))
    tab.setIconUrl(ICON)
    tab.setUrl(QUrl("https://other.example.net/"))
    assert tab.iconUrl.isEmpty()


def test_navigating_within_the_site_keeps_the_icon(model: TabModel) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("https://example.org/page"))
    tab.setIconUrl(ICON)
    tab.setUrl(QUrl("https://example.org/other"))
    assert tab.iconUrl == ICON
