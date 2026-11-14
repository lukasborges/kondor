from PySide6.QtCore import QDate, QDateTime, QTime

from kondor.history.historymanager import HistoryManager
from pytests.history.historyrows import add_visit, now_ms


def local_midnight() -> int:
    return int(QDateTime(QDate.currentDate(), QTime(0, 0)).toMSecsSinceEpoch())


def test_suggest_matches_url_and_title(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://kde.org/", "KDE Community", now - 1000)
    add_visit("https://plasma.kde.org/", "Plasma", now - 2000)
    by_url = history.suggest("plasma")
    assert by_url == [{"type": "history", "url": "https://plasma.kde.org/", "title": "Plasma"}]
    by_title = history.suggest("community")
    assert [row["url"] for row in by_title] == ["https://kde.org/"]
    assert history.suggest("   ") == []


def test_suggest_sorts_by_visits_and_limit(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://a.example/", "Example A", now - 3000)
    add_visit("https://b.example/", "Example B", now - 2000)
    add_visit("https://b.example/", "Example B", now - 1000)
    every = history.suggest("example")
    assert [row["url"] for row in every] == ["https://b.example/", "https://a.example/"]
    assert len(history.suggest("example", 1)) == 1


def test_suggest_escapes_wildcards(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://example.org/100%25", "Percent", now - 1000)
    add_visit("https://example.org/other", "Other", now - 2000)
    assert len(history.suggest("%")) == 1
    assert len(history.suggest("000_")) == 0


def test_host_completion_prefers_most_visited_host(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://www.kde.org/", "KDE", now - 2000)
    add_visit("https://kde.org/announcements/", "KDE news", now - 1000)
    add_visit("https://example.org/kde-guide", "Guide", now - 3000)
    assert history.hostCompletion("kd") == "kde.org"
    assert history.hostCompletion("kde.o") == "kde.org"
    assert history.hostCompletion("kde.org") == ""
    assert history.hostCompletion("kde p") == ""
    assert history.hostCompletion("zzz") == ""


def test_recent_today_excludes_yesterday(history: HistoryManager) -> None:
    midnight = local_midnight()
    add_visit("https://old.example/", "Old", midnight - 1000)
    add_visit("https://a.example/", "A", midnight + 1000)
    add_visit("https://b.example/", "B", midnight + 2000)
    add_visit("https://a.example/", "A", midnight + 3000)
    today = history.recentToday(8)
    assert [row["url"] for row in today] == ["https://a.example/", "https://b.example/"]
    assert len(history.recentToday(1)) == 1
