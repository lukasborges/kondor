from pathlib import Path

from PySide6.QtCore import QUrl

from tests.bookmarks.bookmarkrows import (
    add_folder_in_other,
    add_folder_with_page,
    add_page,
    add_search_fixture,
    manager,
    parent_of,
    reordered_folder,
)

PAGE_URL = QUrl("https://bookmarks.example/page")
UNKNOWN_ID = 999999
REORDERED_SIZE = 2


def test_root_folders(fresh_bookmarks: Path) -> None:
    toolbar, other = manager().toolbarFolderId(), manager().otherFolderId()
    assert toolbar > 0
    assert other > 0
    assert toolbar != other
    assert manager().toolbar_model().folder_id() == toolbar


def test_add_and_find_bookmarks(fresh_bookmarks: Path) -> None:
    assert not manager().isBookmarked(PAGE_URL)
    other = manager().otherFolderId()
    first = manager().addBookmark(PAGE_URL, "Page", other)
    assert first > 0
    assert manager().isBookmarked(PAGE_URL)
    assert manager().bookmarkIdFor(PAGE_URL) == first
    toolbar = manager().toolbarFolderId()
    toolbar_children = manager().childCount(toolbar)
    second = manager().addBookmark(PAGE_URL, "Page again", toolbar)
    assert second > 0
    assert second != first
    assert manager().childCount(toolbar) == toolbar_children + 1
    info = manager().bookmark(first)
    assert info["parentId"] == other
    assert info["title"] == "Page"


def test_search_bookmarks_finds_titles_and_urls(fresh_bookmarks: Path) -> None:
    add_search_fixture()
    assert manager().search("searchable") == [
        {"type": "bookmark", "title": "Searchable Site", "url": "https://searchable.example/"}
    ]
    by_url = manager().search("unique-url")
    assert [row["title"] for row in by_url] == ["Other"]
    assert manager().search("Search folder") == []
    assert len(manager().search("e", 1)) == 1
    assert manager().search("   ") == []


def test_move_between_folders(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("Moved")
    assert folder > 0
    row_id = add_page(manager().otherFolderId(), "Move me", "move")
    assert row_id > 0
    manager().move(row_id, folder, -1)
    assert parent_of(row_id) == folder
    assert manager().childCount(folder) == 1


def test_sorting_inside_a_folder_moves_the_second_item_above_the_first(
    fresh_bookmarks: Path,
) -> None:
    reordered = reordered_folder()
    assert min(reordered) > 0
    contents = manager().folderContents(reordered.folder)
    assert len(contents) == REORDERED_SIZE
    assert contents[0]["id"] == reordered.moved_to_top


def test_model_reports_the_moved_row(fresh_bookmarks: Path) -> None:
    reordered = reordered_folder()
    model = manager().modelForFolder(reordered.folder)
    assert model.rowOf(reordered.moved_to_top) == 0
    assert model.idAt(0) == reordered.moved_to_top
    assert model.rowOf(reordered.pushed_down) == 1
    assert model.rowOf(UNKNOWN_ID) == -1


def test_folder_cannot_move_into_itself(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("Self")
    assert folder > 0
    manager().move(folder, folder, 0)
    assert parent_of(folder) == manager().otherFolderId()


def test_move_into_another_folder_at_end(fresh_bookmarks: Path) -> None:
    target = add_folder_with_page("Move target", "End A", "end-a")
    source = add_folder_with_page("Move source", "End B", "end-b")
    assert min(target + source) > 0
    manager().move(source.page, target.folder, manager().childCount(target.folder))
    assert parent_of(source.page) == target.folder
    assert manager().bookmark(source.page)["position"] == 1
    assert manager().childCount(source.folder) == 0
    model = manager().modelForFolder(target.folder)
    assert model.rowOf(target.page) == 0
    assert model.rowOf(source.page) == 1


def test_refuse_moving_folder_into_child(fresh_bookmarks: Path) -> None:
    parent = add_folder_in_other("Cycle parent")
    assert parent > 0
    child = manager().addFolder("Cycle child", parent)
    assert child > 0
    grandchild = manager().addFolder("Cycle grandchild", child)
    assert grandchild > 0
    manager().move(parent, grandchild, 0)
    assert parent_of(parent) == manager().otherFolderId()
    assert parent_of(child) == parent
    assert parent_of(grandchild) == child


def test_model_follows_selected_folder(fresh_bookmarks: Path) -> None:
    toolbar = manager().toolbarFolderId()
    folder = manager().addFolder("Model folder", toolbar)
    assert folder > 0
    model = manager().modelForFolder(folder)
    assert model is not manager().toolbar_model()
    assert model.folder_id() == folder
    assert model.rowCount() == 0
    assert manager().modelForFolder(toolbar) is manager().toolbar_model()


def test_remove_folder_cascades(fresh_bookmarks: Path) -> None:
    doomed = add_folder_with_page("Doomed", "Doomed page", "doomed")
    assert min(doomed) > 0
    manager().remove(doomed.folder)
    assert manager().bookmark(doomed.folder) == {}
    assert not manager().isBookmarked(QUrl("https://bookmarks.example/doomed"))
    manager().remove(manager().toolbarFolderId())
    assert manager().toolbarFolderId() > 0
