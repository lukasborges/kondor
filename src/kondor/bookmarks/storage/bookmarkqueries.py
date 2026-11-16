from collections.abc import Callable, Sequence
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtSql import QSqlQuery

from kondor.bookmarks.storage.bookmarkcolumns import flag_at, integer_at, text_at
from kondor.core.database import sql

Row = dict[str, Any]
RowReader = Callable[[QSqlQuery], Row]
SEARCH_STATEMENT = (
    "SELECT url, title FROM bookmarks"
    " WHERE is_folder = 0 AND (url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')"
    " ORDER BY (title LIKE ? ESCAPE '\\') DESC, title COLLATE NOCASE, id LIMIT ?"
)
RECENTLY_USED_STATEMENT = (
    "SELECT bookmarks.url, bookmarks.title, MIN(bookmarks.id) FROM bookmarks"
    " JOIN history ON history.url = bookmarks.url WHERE bookmarks.is_folder = 0"
    " GROUP BY bookmarks.url ORDER BY MAX(history.visited_at) DESC, MIN(bookmarks.id) LIMIT ?"
)


def read_rows(statement: str, values: Sequence[object], reader: RowReader) -> list[Row]:
    rows: list[Row] = []
    query = sql.run(statement, values)
    while query is not None and query.next():
        rows.append(reader(query))
    return rows


def read_folder_entry(query: QSqlQuery) -> Row:
    return {
        "id": integer_at(query, 0),
        "title": text_at(query, 1),
        "url": text_at(query, 2),
        "isFolder": flag_at(query, 3),
    }


def read_bookmark(query: QSqlQuery) -> Row:
    return {
        "id": integer_at(query, 0),
        "parentId": integer_at(query, 1),
        "title": text_at(query, 2),
        "url": text_at(query, 3),
        "isFolder": flag_at(query, 4),
        "position": integer_at(query, 5),
        "special": text_at(query, 6),
    }


def read_search_result(query: QSqlQuery) -> Row:
    return {"type": "bookmark", "url": text_at(query, 0), "title": text_at(query, 1)}


def bookmark(row_id: int) -> Row:
    if row_id <= 0:
        return {}
    rows = read_rows(
        "SELECT id, parent_id, title, url, is_folder, position, special"
        " FROM bookmarks WHERE id = ?",
        (row_id,),
        read_bookmark,
    )
    return rows[0] if rows else {}


def folder_contents(folder_id: int) -> list[Row]:
    if folder_id <= 0:
        return []
    return read_rows(
        "SELECT id, title, url, is_folder FROM bookmarks WHERE parent_id = ? ORDER BY position, id",
        (folder_id,),
        read_folder_entry,
    )


def child_count(folder_id: int) -> int:
    if folder_id <= 0:
        return 0
    query = sql.run("SELECT COUNT(*) FROM bookmarks WHERE parent_id = ?", (folder_id,))
    return integer_at(query, 0) if query is not None and query.next() else 0


def like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search(text: str, limit: int) -> list[Row]:
    needle = text.strip()
    if not needle or limit <= 0:
        return []
    pattern = like_pattern(needle)
    values = (pattern, pattern, pattern, limit)
    return read_rows(SEARCH_STATEMENT, values, read_search_result)


def recently_used(limit: int) -> list[Row]:
    if limit <= 0:
        return []
    return read_rows(RECENTLY_USED_STATEMENT, (limit,), read_search_result)


def first_id_or_missing(found: list[int]) -> int:
    return found[0] if found else -1


def bookmark_id_for(url: QUrl) -> int:
    if url.isEmpty():
        return -1
    return first_id_or_missing(
        sql.ids(
            "SELECT id FROM bookmarks WHERE is_folder = 0 AND url = ? ORDER BY id LIMIT 1",
            (url.toString(),),
        )
    )


def is_bookmarked(url: QUrl) -> bool:
    return bookmark_id_for(url) > 0


def special_folder_id(special: str) -> int:
    return first_id_or_missing(
        sql.ids("SELECT id FROM bookmarks WHERE special = ? LIMIT 1", (special,))
    )
