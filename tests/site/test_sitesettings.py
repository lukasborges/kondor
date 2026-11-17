from pytestqt.qtbot import QtBot

from kondor.core.database import sql
from kondor.site.sitesettings import SiteSettings

ROW_COUNT = "SELECT COUNT(*) FROM site_settings"
KEEP_USER_AGENT = "UPDATE site_settings SET user_agent = 'Custom' WHERE host = 'kde.org'"


def row_count() -> int:
    query = sql.run(ROW_COUNT)
    assert query is not None and query.next()
    return int(query.value(0))


def test_sites_start_without_the_exception(site_settings: SiteSettings) -> None:
    assert not site_settings.popupsAllowed("kde.org")


def test_stores_the_exception_for_one_host(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("kde.org", True)
    assert site_settings.popupsAllowed("kde.org")
    assert not site_settings.popupsAllowed("www.kde.org")


def test_hosts_are_compared_in_lower_case(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("KDE.org", True)
    assert site_settings.popupsAllowed("kde.ORG")
    assert site_settings.hostsWithPopupsAllowed() == ["kde.org"]


def test_revoking_deletes_the_row(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("kde.org", True)
    site_settings.setPopupsAllowed("kde.org", False)
    assert row_count() == 0


def test_revoking_keeps_a_row_that_still_holds_a_user_agent(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("kde.org", True)
    sql.run(KEEP_USER_AGENT)
    site_settings.setPopupsAllowed("kde.org", False)
    assert row_count() == 1
    assert site_settings.hostsWithPopupsAllowed() == []


def test_lists_the_allowed_hosts_in_order(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("b.example", True)
    site_settings.setPopupsAllowed("a.example", True)
    assert site_settings.hostsWithPopupsAllowed() == ["a.example", "b.example"]


def test_announces_only_real_changes(site_settings: SiteSettings, qtbot: QtBot) -> None:
    with qtbot.waitSignal(site_settings.changed, timeout=1000) as signal:
        site_settings.setPopupsAllowed("kde.org", True)
    assert signal.args == ["kde.org"]
    with qtbot.assertNotEmitted(site_settings.changed):
        site_settings.setPopupsAllowed("kde.org", True)


def test_ignores_an_empty_host(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("", True)
    assert row_count() == 0


def test_stores_the_user_agent_for_one_host(site_settings: SiteSettings) -> None:
    site_settings.setUserAgent("KDE.org", "Custom/1")
    assert site_settings.userAgent("kde.org") == "Custom/1"
    assert site_settings.userAgent("www.kde.org") == ""
    assert site_settings.hostsWithUserAgent() == ["kde.org"]


def test_clearing_the_user_agent_deletes_the_row(site_settings: SiteSettings) -> None:
    site_settings.setUserAgent("kde.org", "Custom/1")
    site_settings.setUserAgent("kde.org", "")
    assert row_count() == 0


def test_clearing_the_user_agent_keeps_the_pop_up_exception(site_settings: SiteSettings) -> None:
    site_settings.setPopupsAllowed("kde.org", True)
    site_settings.setUserAgent("kde.org", "Custom/1")
    site_settings.setUserAgent("kde.org", "")
    assert site_settings.popupsAllowed("kde.org")
