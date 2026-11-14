from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.bookmarks.bookmarkmanager import BookmarkManager
from kondor.browser.profile.profilemanager import ProfileManager
from pytests.browser.address.suggestionpopup import (
    add_history,
    add_plasma_bookmark,
    add_plasma_history,
    clear_history,
    field_of,
    has_row_labeled,
    has_row_with_icon,
    popup_component,
    rows_of,
)
from pytests.browser.address.suggestionpopup import popup_typing as create_popup

Typing = Callable[[str], QObject]
MAX_ROWS = 10
VISIT_AND_SEARCH_ROWS = 2
ROWS_WITH_A_MATCH = 3


@pytest.fixture
def popup_typing(kondor_engine: QQmlEngine, staged_build: Path) -> Iterator[Typing]:
    clear_history()
    component = popup_component(kondor_engine, staged_build)
    popups: list[QObject] = []

    def typing(text: str) -> QObject:
        popups.append(create_popup(component, text))
        return popups[-1]

    yield typing
    for popup in popups:
        popup.deleteLater()


@pytest.fixture
def seeded_plasma(kondor_types: None) -> Iterator[None]:
    add_plasma_history()
    folder = add_plasma_bookmark()
    yield
    BookmarkManager.instance().remove(folder)


def test_visit_row_comes_first(popup_typing: Typing) -> None:
    rows = rows_of(popup_typing("kde.org"))
    assert len(rows) >= VISIT_AND_SEARCH_ROWS
    assert field_of(rows, 0, "url") == "https://kde.org"
    assert field_of(rows, 0, "suffix") == "Visit"
    assert field_of(rows, 0, "fieldText") == "https://kde.org"


def test_search_row_follows_the_visit_row(popup_typing: Typing) -> None:
    rows = rows_of(popup_typing("kde.org"))
    assert len(rows) >= VISIT_AND_SEARCH_ROWS
    assert field_of(rows, 1, "iconName") == "edit-find"
    assert field_of(rows, 1, "url").startswith("https://duckduckgo.com/")


def test_search_row_shows_the_typed_text(popup_typing: Typing) -> None:
    popup = popup_typing("kde.org")
    assert field_of(rows_of(popup), 1, "fieldText") == "kde.org"
    selected = QMetaObject.invokeMethod(
        popup, "selectedText", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", 1)
    )
    assert selected == "kde.org"


def test_plain_word_offers_only_the_search_row(popup_typing: Typing) -> None:
    rows = rows_of(popup_typing("plasma"))
    assert len(rows) == 1
    assert field_of(rows, 0, "suffix") == "Search with DuckDuckGo"


def test_blank_text_has_no_rows(popup_typing: Typing) -> None:
    assert rows_of(popup_typing("   ")) == []


def test_adds_bookmark_rows(popup_typing: Typing, seeded_plasma: None) -> None:
    rows = rows_of(popup_typing("plasma"))
    assert has_row_with_icon(rows, "bookmarks")
    assert has_row_labeled(rows, "Plasma HIG", "bookmarks")


def test_adds_history_rows(popup_typing: Typing, seeded_plasma: None) -> None:
    assert has_row_with_icon(rows_of(popup_typing("plasma")), "view-history")


def test_adds_network_suggestion_rows(popup_typing: Typing, seeded_plasma: None) -> None:
    popup = popup_typing("plasma")
    before = len(rows_of(popup))
    popup.setProperty("networkSuggestions", ["kde connect", "kde plasma 6"])
    rows = rows_of(popup)
    assert len(rows) == before + 2
    assert field_of(rows, -1, "label") == "kde plasma 6"
    assert field_of(rows, -1, "fieldText") == "kde plasma 6"
    expected = ProfileManager.instance().searchUrl("kde plasma 6").toString()
    assert field_of(rows, -1, "url") == expected


def test_editing_the_text_drops_network_suggestions(
    popup_typing: Typing, seeded_plasma: None
) -> None:
    popup = popup_typing("plasma")
    popup.setProperty("networkSuggestions", ["kde connect"])
    assert has_row_labeled(rows_of(popup), "kde connect")
    popup.setProperty("text", "plasma p")
    assert not has_row_labeled(rows_of(popup), "kde connect")


def test_keeps_the_row_order(popup_typing: Typing, seeded_plasma: None) -> None:
    rows = rows_of(popup_typing("plasma"))
    assert len(rows) >= ROWS_WITH_A_MATCH
    assert field_of(rows, 0, "iconName") == "edit-find"


def test_limits_rows_and_skips_duplicates(popup_typing: Typing) -> None:
    for index in range(15):
        add_history(f"https://example{index}.org/", f"Example {index}", 1000000 + index)
    add_history("https://example0.org/", "Example 0", 2000000)
    rows = rows_of(popup_typing("example"))
    urls = [field_of(rows, row, "url") for row in range(len(rows))]
    assert len(rows) <= MAX_ROWS
    assert len(urls) == len(set(urls))


def test_activate_emits_the_row_url(popup_typing: Typing, qtbot: QtBot) -> None:
    popup = popup_typing("example.com")
    rows = rows_of(popup)
    assert len(rows) == VISIT_AND_SEARCH_ROWS
    assert field_of(rows, 0, "url") == "https://example.com"
    with qtbot.waitSignal(popup.navigate, timeout=1000) as blocker:
        QMetaObject.invokeMethod(popup, "activate", Q_ARG("QVariant", 0), Q_ARG("QVariant", True))
    assert blocker.args == [QUrl("https://example.com"), True]
