from PySide6.QtCore import QUrl

from kondor.browser.tabs.closedtabs import ClosedTabs


def closed_tabs(count: int) -> ClosedTabs:
    tabs = ClosedTabs()
    for index in range(count):
        tabs.remember(QUrl(f"https://tab{index}.example/"), f"Tab {index}", index)
    return tabs


def test_lists_newest_first() -> None:
    entries = closed_tabs(2).to_variant_list()
    assert entries == [
        {"url": QUrl("https://tab1.example/"), "title": "Tab 1"},
        {"url": QUrl("https://tab0.example/"), "title": "Tab 0"},
    ]


def test_keeps_at_most_the_limit() -> None:
    tabs = closed_tabs(ClosedTabs.MAX_CLOSED_TABS + 1)
    entries = tabs.to_variant_list()
    assert tabs.size() == ClosedTabs.MAX_CLOSED_TABS
    assert entries[0]["title"] == "Tab 20"
    assert entries[-1]["title"] == "Tab 1"


def test_take_counts_from_the_newest() -> None:
    tabs = closed_tabs(3)
    taken = tabs.take(1)
    assert (taken.url, taken.title, taken.index) == (QUrl("https://tab1.example/"), "Tab 1", 1)
    assert [entry["title"] for entry in tabs.to_variant_list()] == ["Tab 2", "Tab 0"]


def test_is_empty_and_size() -> None:
    tabs = ClosedTabs()
    assert tabs.is_empty()
    assert tabs.size() == 0
    tabs.remember(QUrl("https://kde.org/"), "KDE", 0)
    assert not tabs.is_empty()
    assert tabs.size() == 1
