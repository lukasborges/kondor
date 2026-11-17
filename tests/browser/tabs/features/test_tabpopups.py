from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl

from kondor.browser.tabs.features.tabpopups import MAX_BLOCKED, TabPopups
from kondor.core.settings.settings import Settings
from kondor.site.sitesettings import SiteSettings

PAGE = QUrl("https://Tickets.example.com:8443/checkout")
HOST = "tickets.example.com"
POPUP = "https://pay.example.net/"


@pytest.fixture
def popups(site_settings: SiteSettings) -> Iterator[TabPopups]:
    Settings.instance().setProperty("blockPopups", True)
    group = TabPopups(is_private=False)
    group.update_for(PAGE)
    yield group
    group.deleteLater()


def test_follows_the_host_without_port_in_lower_case(popups: TabPopups) -> None:
    assert popups.host == HOST


def test_lists_blocked_pop_ups_newest_first(popups: TabPopups) -> None:
    popups.add_blocked("https://a.example/")
    popups.add_blocked("https://b.example/")
    assert popups.blockedUrls == ["https://b.example/", "https://a.example/"]


def test_keeps_a_repeated_pop_up_once(popups: TabPopups) -> None:
    popups.add_blocked(POPUP)
    popups.add_blocked(POPUP)
    assert popups.blockedUrls == [POPUP]


def test_keeps_at_most_ten(popups: TabPopups) -> None:
    for number in range(MAX_BLOCKED + 3):
        popups.add_blocked(f"https://p{number}.example/")
    assert len(popups.blockedUrls) == MAX_BLOCKED
    assert popups.blockedUrls[0] == f"https://p{MAX_BLOCKED + 2}.example/"


def test_clear_empties_the_list(popups: TabPopups) -> None:
    popups.add_blocked(POPUP)
    popups.clear()
    assert popups.blockedUrls == []


def test_opening_one_removes_it_and_asks_the_window_to_open_it(popups: TabPopups) -> None:
    popups.add_blocked(POPUP)
    popups.add_blocked("https://other.example/")
    opened: list[str] = []
    popups.openRequested.connect(opened.append)
    popups.openBlocked(POPUP)
    assert opened == [POPUP]
    assert popups.blockedUrls == ["https://other.example/"]


def test_opening_an_unknown_address_does_nothing(popups: TabPopups) -> None:
    opened: list[str] = []
    popups.openRequested.connect(opened.append)
    popups.openBlocked("https://never-blocked.example/")
    assert opened == []


def test_allowing_stores_the_exception_and_stops_listing(popups: TabPopups) -> None:
    popups.setAllowed(True)
    assert popups.isAllowed
    assert SiteSettings.instance().popupsAllowed(HOST)
    popups.add_blocked(POPUP)
    assert popups.blockedUrls == []


def test_revoking_through_the_site_settings_updates_the_tab(popups: TabPopups) -> None:
    popups.setAllowed(True)
    SiteSettings.instance().setPopupsAllowed(HOST, False)
    assert not popups.isAllowed


def test_other_hosts_stay_blocked(popups: TabPopups) -> None:
    popups.setAllowed(True)
    popups.update_for(QUrl("https://other.example/"))
    assert not popups.isAllowed


def test_nothing_is_listed_when_blocking_is_off(popups: TabPopups) -> None:
    Settings.instance().setProperty("blockPopups", False)
    popups.add_blocked(POPUP)
    assert popups.blockedUrls == []


def test_private_tab_reads_exceptions_but_never_writes_them(
    site_settings: SiteSettings,
) -> None:
    SiteSettings.instance().setPopupsAllowed(HOST, True)
    private = TabPopups(is_private=True)
    private.update_for(PAGE)
    assert private.isAllowed
    private.setAllowed(False)
    assert SiteSettings.instance().popupsAllowed(HOST)
    assert not private.canChangeAllowed
