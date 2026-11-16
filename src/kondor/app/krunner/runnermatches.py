from dataclasses import dataclass

from PySide6.QtCore import QUrl

from kondor.app.krunner.opentabs import OpenTab
from kondor.bookmarks.storage import bookmarkqueries
from kondor.history import historysearch

MIN_QUERY_LENGTH = 3
MAX_TABS = 8
MAX_BOOKMARKS = 5
MAX_HISTORY = 5


@dataclass(frozen=True)
class RunnerMatch:
    match_id: str
    kind: str
    title: str
    url: QUrl
    tab: OpenTab | None = None


def tab_matches(tab: OpenTab, words: list[str]) -> bool:
    text = f"{tab.title} {tab.url.toString()}".casefold()
    return all(word in text for word in words)


def tab_results(query: str, tabs: list[OpenTab]) -> list[RunnerMatch]:
    words = query.casefold().split()
    found = [tab for tab in tabs if tab_matches(tab, words)][:MAX_TABS]
    return [RunnerMatch(f"tab-{n}", "tab", tab.title, tab.url, tab) for n, tab in enumerate(found)]


def entry_results(kind: str, entries: list[dict[str, str]]) -> list[RunnerMatch]:
    return [
        RunnerMatch(f"{kind}-{n}", kind, str(entry["title"]), QUrl(str(entry["url"])))
        for n, entry in enumerate(entries)
    ]


def without_urls(matches: list[RunnerMatch], taken: set[QUrl]) -> list[RunnerMatch]:
    return [match for match in matches if match.url not in taken]


def find_matches(query: str, tabs: list[OpenTab]) -> list[RunnerMatch]:
    needle = query.strip()
    if len(needle) < MIN_QUERY_LENGTH:
        return []
    opened = tab_results(needle, tabs)
    bookmarks = entry_results("bookmark", bookmarkqueries.search(needle, MAX_BOOKMARKS))
    bookmarks = without_urls(bookmarks, {match.url for match in opened})
    history = entry_results("history", historysearch.suggest(needle, MAX_HISTORY))
    history = without_urls(history, {match.url for match in opened + bookmarks})
    return opened + bookmarks + history
