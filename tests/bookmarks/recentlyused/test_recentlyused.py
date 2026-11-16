from pathlib import Path

from kondor.core.database import sql
from tests.bookmarks.bookmarkrows import EXAMPLE_SITE, add_folder_in_toolbar, add_page, manager

INSERT_VISIT = "INSERT INTO history (url, title, visited_at) VALUES (?, '', ?)"


def visit(path: str, visited_at: int) -> None:
    assert sql.run(INSERT_VISIT, (EXAMPLE_SITE + path, visited_at)) is not None


def recently_used_titles(limit: int) -> list[str]:
    return [row["title"] for row in manager().recentlyUsedBookmarks(limit)]


def test_lists_the_most_recently_visited_bookmark_first(fresh_bookmarks: Path) -> None:
    toolbar = manager().toolbarFolderId()
    add_page(toolbar, "Old", "old")
    add_page(toolbar, "New", "new")
    visit("new", 10)
    visit("old", 20)
    visit("new", 5)
    assert recently_used_titles(5) == ["Old", "New"]


def test_skips_bookmarks_never_visited_and_folders(fresh_bookmarks: Path) -> None:
    add_page(manager().toolbarFolderId(), "Unvisited", "unvisited")
    add_folder_in_toolbar("Folder")
    assert recently_used_titles(5) == []


def test_lists_a_url_bookmarked_twice_once(fresh_bookmarks: Path) -> None:
    toolbar = manager().toolbarFolderId()
    add_page(toolbar, "Twin", "twin")
    add_page(manager().addFolder("Copy", toolbar), "Twin", "twin")
    visit("twin", 1)
    assert recently_used_titles(5) == ["Twin"]


def test_stops_at_the_limit(fresh_bookmarks: Path) -> None:
    for number in range(3):
        add_page(manager().toolbarFolderId(), f"Page {number}", f"p{number}")
        visit(f"p{number}", number)
    assert recently_used_titles(2) == ["Page 2", "Page 1"]


def test_of_a_non_positive_limit_is_empty(fresh_bookmarks: Path) -> None:
    add_page(manager().toolbarFolderId(), "Page", "page")
    visit("page", 1)
    assert manager().recentlyUsedBookmarks(0) == []
