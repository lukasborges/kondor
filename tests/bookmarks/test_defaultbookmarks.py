from pathlib import Path
from typing import Any

from kondor.core.database.database import Database
from tests.bookmarks.bookmarkrows import (
    COUNT_ALL,
    count_rows,
    count_titled,
    delete_qt_docs_default,
    manager,
    write_version_two_file,
)

SCHEMA_VERSION = 7
VERSION_TWO_ROWS = 3
TOOLBAR_TITLES = ["KDE", "Planet KDE", "Qt Docs", "News", "Development", "Linux"]
TOOLBAR_URLS = ["https://kde.org/", "https://planet.kde.org/", "https://doc.qt.io/"]


def toolbar_rows() -> list[dict[str, Any]]:
    return manager().folderContents(manager().toolbarFolderId())


def folder_rows(folder_row: dict[str, Any]) -> list[dict[str, Any]]:
    return manager().folderContents(folder_row["id"])


def test_toolbar_holds_site_bookmarks_then_folders(fresh_bookmarks: Path) -> None:
    toolbar = toolbar_rows()
    assert [row["title"] for row in toolbar] == TOOLBAR_TITLES
    assert [row["url"] for row in toolbar[:3]] == TOOLBAR_URLS
    assert all(row["isFolder"] for row in toolbar[3:])


def test_default_folders_have_their_sizes(fresh_bookmarks: Path) -> None:
    toolbar = toolbar_rows()
    assert [len(folder_rows(row)) for row in toolbar[3:]] == [6, 6, 7]


def test_default_folders_hold_their_bookmarks(fresh_bookmarks: Path) -> None:
    news, development, linux = (folder_rows(row) for row in toolbar_rows()[3:])
    assert news[0]["title"] == "LWN.net"
    assert news[0]["url"] == "https://lwn.net/"
    assert development[1]["title"] == "KDE Human Interface Guidelines"
    assert linux[-1]["title"] == "KDE Discuss"
    assert linux[-1]["url"] == "https://discuss.kde.org/"


def test_existing_bookmarks_are_not_replaced(fresh_bookmarks: Path) -> None:
    Database.reset_instance()
    fresh_bookmarks.unlink()
    write_version_two_file(fresh_bookmarks)
    assert Database.instance().is_valid()
    assert count_rows("PRAGMA user_version") == SCHEMA_VERSION
    assert count_rows(COUNT_ALL) == VERSION_TWO_ROWS
    assert count_titled("News") == 0
    assert count_titled("Mine") == 1


def test_deleted_defaults_stay_deleted(fresh_bookmarks: Path) -> None:
    Database.reset_instance()
    remaining = delete_qt_docs_default(fresh_bookmarks)
    assert Database.instance().is_valid()
    assert count_titled("Qt Docs") == 0
    assert count_rows(COUNT_ALL) == remaining


def test_other_bookmarks_move_to_the_end_of_the_toolbar(fresh_bookmarks: Path) -> None:
    Database.reset_instance()
    fresh_bookmarks.unlink()
    write_version_two_file(fresh_bookmarks)
    assert Database.instance().is_valid()
    assert [row["title"] for row in toolbar_rows()] == ["Mine", "Was other"]
    assert count_rows("SELECT COUNT(*) FROM bookmarks WHERE special = 'other'") == 0
