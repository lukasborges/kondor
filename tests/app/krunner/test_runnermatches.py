from pathlib import Path

from PySide6.QtCore import QUrl

from kondor.app.krunner.opentabs import OpenTab, open_tabs
from kondor.app.krunner.runnermatches import find_matches
from kondor.bookmarks.bookmarkmanager import BookmarkManager
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow
from tests.history.historyrows import add_visit, now_ms


def tabs_of(*tabs: FakeTab) -> list[OpenTab]:
    window = FakeWindow(list(tabs))
    return open_tabs([window])


def bookmark(url: str, title: str) -> None:
    folder = BookmarkManager.instance().toolbarFolderId()
    assert BookmarkManager.instance().addBookmark(QUrl(url), title, folder) > 0


def ids(query: str, tabs: list[OpenTab]) -> list[str]:
    return [match.match_id for match in find_matches(query, tabs)]


def test_short_queries_give_nothing(fresh_database: Path) -> None:
    assert find_matches("kd", tabs_of(FakeTab("KDE", "https://kde.org"))) == []


def test_tab_matches_by_title_and_by_url(fresh_database: Path) -> None:
    tabs = tabs_of(FakeTab("Plasma", "https://kde.org"), FakeTab("Other", "https://example.com"))

    assert ids("plas", tabs) == ["tab-0"]
    assert ids("example", tabs) == ["tab-0"]


def test_every_word_must_match_ignoring_case(fresh_database: Path) -> None:
    tabs = tabs_of(FakeTab("Plasma Desktop", "https://kde.org"))

    assert ids("PLASMA kde", tabs) == ["tab-0"]
    assert ids("plasma qt.io", tabs) == []


def test_order_is_tabs_then_bookmarks_then_history(fresh_database: Path) -> None:
    bookmark("https://bm.example/", "Sample bookmark")
    add_visit("https://hist.example/", "Sample history", now_ms())
    tabs = tabs_of(FakeTab("Sample tab", "https://tab.example/"))

    assert ids("sample", tabs) == ["tab-0", "bookmark-0", "history-0"]


def test_results_are_limited_per_group(fresh_database: Path) -> None:
    for n in range(10):
        bookmark(f"https://b{n}.example/", f"Limit bookmark {n}")
        add_visit(f"https://h{n}.example/", f"Limit history {n}", now_ms())
    tabs = tabs_of(*[FakeTab(f"Limit tab {n}", f"https://t{n}.example/") for n in range(12)])

    found = ids("limit", tabs)

    assert [found.count(f"{kind}-0") for kind in ("tab", "bookmark", "history")] == [1, 1, 1]
    assert len(found) == 8 + 5 + 5


def test_urls_are_not_repeated(fresh_database: Path) -> None:
    bookmark("https://open.example/", "Dup open")
    bookmark("https://marked.example/", "Dup marked")
    add_visit("https://marked.example/", "Dup marked", now_ms())
    add_visit("https://open.example/", "Dup open", now_ms())
    tabs = tabs_of(FakeTab("Dup open", "https://open.example/"))

    assert ids("dup", tabs) == ["tab-0", "bookmark-0"]
