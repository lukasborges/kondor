from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QUrl
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from kondor.bookmarks.bookmarkmanager import BookmarkManager
from kondor.core.database import sql

EXAMPLE_SITE = "https://bookmarks.example/"
SEPARATE_CONNECTION = "bookmarks-test"
COUNT_TITLED = "SELECT COUNT(*) FROM bookmarks WHERE title = ?"
COUNT_ALL = "SELECT COUNT(*) FROM bookmarks"
VERSION_TWO_STATEMENTS = (
    "CREATE TABLE bookmarks ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
    "  is_folder INTEGER NOT NULL DEFAULT 0,"
    "  title TEXT NOT NULL DEFAULT '',"
    "  url TEXT,"
    "  position INTEGER NOT NULL DEFAULT 0,"
    "  created_at INTEGER NOT NULL,"
    "  special TEXT"
    ")",
    "INSERT INTO bookmarks (parent_id, is_folder, title, url, position, created_at, special) VALUES"
    " (NULL, 1, 'Bookmarks Toolbar', NULL, 0, 1, 'toolbar'),"
    " (NULL, 1, 'Other Bookmarks', NULL, 0, 1, 'other'),"
    " (1, 0, 'Mine', 'https://mine.example/', 0, 1, NULL),"
    " (2, 0, 'Was other', 'https://other.example/', 0, 1, NULL)",
    "PRAGMA user_version = 2",
)
DELETE_QT_DOCS = "DELETE FROM bookmarks WHERE title = 'Qt Docs' AND url = 'https://doc.qt.io/'"


class FolderWithPage(NamedTuple):
    folder: int
    page: int


class ReorderedFolder(NamedTuple):
    folder: int
    moved_to_top: int
    pushed_down: int


def manager() -> BookmarkManager:
    return BookmarkManager.instance()


def add_page(folder_id: int, title: str, path: str) -> int:
    return manager().addBookmark(QUrl(EXAMPLE_SITE + path), title, folder_id)


def add_folder_in_toolbar(title: str) -> int:
    return manager().addFolder(title, manager().toolbarFolderId())


def parent_of(row_id: int) -> int:
    return int(manager().bookmark(row_id)["parentId"])


def add_folder_with_page(folder_title: str, page_title: str, path: str) -> FolderWithPage:
    folder = add_folder_in_toolbar(folder_title)
    return FolderWithPage(folder, add_page(folder, page_title, path))


def reordered_folder() -> ReorderedFolder:
    folder = add_folder_in_toolbar("Moved")
    pushed_down = add_page(folder, "Move me", "move")
    second = add_page(folder, "Second", "second")
    manager().move(second, folder, 0)
    return ReorderedFolder(folder, second, pushed_down)


def add_search_fixture() -> None:
    folder = add_folder_in_toolbar("Search folder")
    assert manager().addBookmark(QUrl("https://searchable.example/"), "Searchable Site", folder) > 0
    assert manager().addBookmark(QUrl("https://other.example/unique-url"), "Other", folder) > 0


def count_rows(statement: str, values: Sequence[object] = ()) -> int:
    query = sql.run(statement, values)
    return int(query.value(0)) if query is not None and query.next() else -1


def count_titled(title: str) -> int:
    return count_rows(COUNT_TITLED, (title,))


@contextmanager
def separate_query(path: Path) -> Iterator[QSqlQuery]:
    connection = QSqlDatabase.addDatabase("QSQLITE", SEPARATE_CONNECTION)
    connection.setDatabaseName(str(path))
    assert connection.open()
    query = QSqlQuery(connection)
    yield query
    query.finish()
    del query
    connection.close()
    del connection
    QSqlDatabase.removeDatabase(SEPARATE_CONNECTION)


def write_version_two_file(path: Path) -> None:
    with separate_query(path) as query:
        for statement in VERSION_TWO_STATEMENTS:
            assert query.exec(statement)


def separate_count(query: QSqlQuery, statement: str) -> int:
    assert query.exec(statement) and query.next()
    return int(query.value(0))


def delete_qt_docs_default(path: Path) -> int:
    with separate_query(path) as query:
        assert separate_count(query, "SELECT COUNT(*) FROM bookmarks WHERE title = 'Qt Docs'") == 1
        assert query.exec(DELETE_QT_DOCS)
        return separate_count(query, COUNT_ALL)
