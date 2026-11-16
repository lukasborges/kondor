from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine

from tests.bookmarks.bookmarkrows import add_page, manager
from tests.bookmarks.recentlyused.test_recentlyused import visit
from tests.qmlsupport import captured_messages, error_text, load_component

ENTRIES_QML = """
import QtQml
import Kondor

BookmarksPanelEntries {
    property var titles: entries.map(function(entry) { return entry.title })
    property var sections: entries.map(function(entry) { return entry.section })
}
"""


def create_entries(engine: QQmlEngine) -> tuple[QQmlComponent, QObject]:
    component = load_component(engine, ENTRIES_QML)
    created = component.create()
    assert created is not None, error_text(component)
    return component, created


def test_overview_lists_recently_used_then_the_toolbar_contents(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    add_page(manager().toolbarFolderId(), "Visited", "visited")
    visit("visited", 1)
    with captured_messages() as messages:
        _component, entries = create_entries(kondor_engine)
    assert messages == []
    assert entries.property("titles").toVariant()[0] == "Visited"
    assert entries.property("sections").toVariant()[0] == "Recently Used"
    assert entries.property("sections").toVariant()[-1] == "Bookmarks Toolbar"


def test_search_replaces_the_overview_with_matching_bookmarks(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    add_page(manager().toolbarFolderId(), "Needle page", "needle")
    component, entries = create_entries(kondor_engine)
    entries.setProperty("query", "needle")
    assert entries.property("titles").toVariant() == ["Needle page"]
    assert component.isReady()
