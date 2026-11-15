from kondor.core.settings.settings import Settings
from kondor.history.historymanager import HistoryManager
from tests.history.historyrows import add_grouped_visits, add_visit, now_ms

NINETY_ONE_DAYS_MS = 91 * 24 * 60 * 60 * 1000
TWO_SITES = 2


def hosts_of(sites: list[dict[str, str]]) -> list[str]:
    return [site["host"] for site in sites]


def test_groups_by_host_and_sorts_by_visits(history: HistoryManager) -> None:
    add_grouped_visits()
    sites = history.topSites(8)
    assert hosts_of(sites) == ["kde.org", "wikipedia.org", "fedoraproject.org"]
    assert sites[0]["url"] == "https://kde.org/a"
    assert sites[0]["title"] == "A latest"
    assert len(history.topSites(TWO_SITES)) == TWO_SITES


def test_strips_www_and_ignores_other_schemes(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://www.example.org/page", "Example", now - 1000)
    add_visit("file:///tmp/page.html", "Local", now - 2000)
    add_visit("about:blank", "Blank", now - 3000)
    assert hosts_of(history.topSites(8)) == ["example.org"]


def test_skips_hidden_hosts(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://kde.org/", "KDE", now - 1000)
    add_visit("https://wikipedia.org/", "Wiki", now - 2000)
    Settings.instance().setProperty("hiddenTopSites", ["kde.org"])
    assert hosts_of(history.topSites(8)) == ["wikipedia.org"]


def test_ignores_visits_older_than_ninety_days(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://old.example/", "Old", now - NINETY_ONE_DAYS_MS)
    add_visit("https://new.example/", "New", now - 1000)
    assert hosts_of(history.topSites(8)) == ["new.example"]
