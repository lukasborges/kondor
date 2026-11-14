from pathlib import Path

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.bookmarks.bookmarkmodel import BookmarkModel
from pytests.bookmarks.bookmarkrows import add_folder_in_other, add_page, manager

OUTSIDE_ROWS = (-1, 99)
UNKNOWN_ID = 999999


def model_of(folder_id: int) -> BookmarkModel:
    model = BookmarkModel()
    model.folderId = folder_id
    return model


def test_filter_matches_title_or_url_and_escapes_wildcards(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("Filtered")
    linux = add_page(folder, "100% Linux", "linux")
    add_page(folder, "Other", "other")
    model = model_of(folder)
    model.filter = "%"
    assert model.count == 1
    assert model.idAt(0) == linux


def test_accessors_are_empty_outside_the_rows(fresh_bookmarks: Path) -> None:
    model = model_of(manager().toolbarFolderId())
    assert model.urlAt(0) == "https://kde.org/"
    assert [model.urlAt(row) for row in OUTSIDE_ROWS] == ["", ""]
    assert [model.idAt(row) for row in OUTSIDE_ROWS] == [-1, -1]
    assert [model.isFolderAt(row) for row in OUTSIDE_ROWS] == [False, False]
    assert model.rowOf(UNKNOWN_ID) == -1


def test_negative_folder_id_has_no_rows(fresh_bookmarks: Path) -> None:
    assert BookmarkModel().count == 0
    assert model_of(-5).count == 0


def test_change_refreshes_folder_models(fresh_bookmarks: Path, qtbot: QtBot) -> None:
    other = manager().otherFolderId()
    model = manager().modelForFolder(other)
    with qtbot.waitSignal(model.countChanged):
        manager().addBookmark(QUrl("https://kde.org/"), "KDE", other)
    assert model.count == 1
    assert model.urlAt(0) == "https://kde.org/"
