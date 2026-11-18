from PySide6.QtCore import QUrl

from kondor.app.windows import tabsearch
from kondor.app.windows.tabsearchtext import address_without_scheme, highlight
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow


def window_of(*pages: tuple[str, str], private: bool = False) -> FakeWindow:
    return FakeWindow([FakeTab(title, url, private) for title, url in pages], private)


def titles(found: list[dict[str, object]]) -> list[object]:
    return [entry["titleHtml"] for entry in found]


def test_lists_this_window_first_then_the_numbered_others(qapp: object) -> None:
    first = window_of(("A", "https://a.example/"))
    second = window_of(("B", "https://b.example/"))
    third = window_of(("C", "https://c.example/"))

    found = tabsearch.search([first, second, third], second, "")

    assert [entry["windowNumber"] for entry in found] == [1, 2, 3]
    assert titles(found) == ["B", "A", "C"]


def test_a_normal_window_never_lists_private_tabs(qapp: object) -> None:
    normal = window_of(("A", "https://a.example/"))
    private = window_of(("Secret", "https://s.example/"), private=True)

    assert titles(tabsearch.search([normal, private], normal, "")) == ["A"]


def test_a_private_window_lists_only_its_own_tabs(qapp: object) -> None:
    normal = window_of(("A", "https://a.example/"))
    private = window_of(("Secret", "https://s.example/"), private=True)

    assert titles(tabsearch.search([normal, private], private, "")) == ["Secret"]


def test_filters_by_every_word_in_title_or_address(qapp: object) -> None:
    window = window_of(
        ("Kirigami documentation", "https://develop.kde.org/docs"),
        ("Qt overview", "https://doc.qt.io/"),
    )

    found = tabsearch.search([window], window, "KDE doc")

    assert len(found) == 1
    assert found[0]["addressHtml"] == "develop.<b>kde</b>.org/<b>doc</b>s"


def test_matches_are_bold_and_html_is_escaped() -> None:
    assert highlight("a <b> & kde", ["kde", "b"]) == "a &lt;<b>b</b>&gt; &amp; <b>kde</b>"


def test_addresses_drop_the_scheme_and_a_lone_slash() -> None:
    assert address_without_scheme(QUrl("https://kde.org/")) == "kde.org"
    assert address_without_scheme(QUrl("https://kde.org/a/")) == "kde.org/a/"
