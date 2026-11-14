from PySide6.QtCore import QUrl

from kondor.history.historymanager import HistoryManager
from pytests.history.historyrows import add_visit, id_of_title, now_ms, titles


def test_add_visit_ignores_unsupported_schemes(history: HistoryManager) -> None:
    history.addVisit(QUrl("about:blank"), "Blank")
    history.addVisit(QUrl("ftp://example.org/"), "Ftp")
    history.addVisit(QUrl(), "Empty")
    assert titles() == []
    history.addVisit(QUrl("https://example.org/"), "Web")
    assert titles() == ["Web"]


def test_revisit_within_window_updates_title_only(history: HistoryManager) -> None:
    url = QUrl("https://example.org/")
    history.addVisit(url, "First")
    history.addVisit(url, "Second")
    assert titles() == ["Second"]


def test_update_title_leaves_older_visits_untouched(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://example.org/", "Old", now - 60000)
    add_visit("https://example.org/", "Recent", now - 1000)
    history.updateTitle(QUrl("https://example.org/"), "Renamed")
    assert titles() == ["Old", "Renamed"]


def test_clear_since_keeps_older_visits(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://a.example/", "Older", now - 5000)
    add_visit("https://b.example/", "Newer", now - 1000)
    history.clearSince(now - 2000)
    assert titles() == ["Older"]


def test_remove_entry_deletes_only_that_row(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://a.example/", "Keep", now - 5000)
    add_visit("https://b.example/", "Drop", now - 1000)
    history.removeEntry(id_of_title("Drop"))
    assert titles() == ["Keep"]
