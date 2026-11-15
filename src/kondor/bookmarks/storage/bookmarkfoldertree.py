from collections.abc import Sequence

from PySide6.QtCore import QDateTime, qWarning

from kondor.bookmarks.bookmarkrow import BookmarkRow
from kondor.bookmarks.storage.bookmarkcolumns import integer_at
from kondor.core.database import sql

IN_SUBTREE_STATEMENT = (
    "WITH RECURSIVE subtree(id) AS ("
    "  SELECT id FROM bookmarks WHERE id = ?"
    "  UNION ALL"
    "  SELECT b.id FROM bookmarks b JOIN subtree s ON b.parent_id = s.id"
    ") SELECT 1 FROM subtree WHERE id = ? LIMIT 1"
)
REMOVE_SUBTREE_STATEMENT = (
    "WITH RECURSIVE doomed(id) AS ("
    "  SELECT id FROM bookmarks WHERE id = ?"
    "  UNION ALL"
    "  SELECT b.id FROM bookmarks b JOIN doomed d ON b.parent_id = d.id"
    ") DELETE FROM bookmarks WHERE id IN (SELECT id FROM doomed)"
)


def siblings_condition(parent_id: int) -> str:
    return "parent_id = ?" if parent_id > 0 else "parent_id IS NULL"


def siblings_values(parent_id: int) -> Sequence[object]:
    return (parent_id,) if parent_id > 0 else ()


def sibling_ids(parent_id: int) -> list[int]:
    return sql.ids(
        "SELECT id FROM bookmarks WHERE "
        + siblings_condition(parent_id)
        + " ORDER BY position, id",
        siblings_values(parent_id),
    )


def placed_at(order: list[int], moved_id: int, moved_position: int) -> list[int]:
    others = [row_id for row_id in order if row_id != moved_id]
    size = len(others)
    others.insert(size if moved_position < 0 else max(0, min(moved_position, size)), moved_id)
    return others


def insert_values(row: BookmarkRow) -> Sequence[object]:
    url = None if row.is_folder or not row.url.isValid() else row.url.toString()
    folder_flag = 1 if row.is_folder else 0
    created_at = QDateTime.currentMSecsSinceEpoch()
    return (sql.id_or_null(row.parent_id), folder_flag, row.title, url, row.position, created_at)


def is_in_subtree(folder_id: int, ancestor_id: int) -> bool:
    return bool(sql.ids(IN_SUBTREE_STATEMENT, (ancestor_id, folder_id)))


def renumber(parent_id: int, moved_id: int, moved_position: int) -> None:
    order = sibling_ids(parent_id)
    if moved_id > 0:
        order = placed_at(order, moved_id, moved_position)
    for position, row_id in enumerate(order):
        sql.run("UPDATE bookmarks SET position = ? WHERE id = ?", (position, row_id))


def first_free_position(parent_id: int) -> int:
    query = sql.run(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM bookmarks WHERE "
        + siblings_condition(parent_id),
        siblings_values(parent_id),
    )
    return integer_at(query, 0) if query is not None and query.next() else 0


def insert_row(row: BookmarkRow) -> int:
    query = sql.run(
        "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
        " created_at) VALUES (?, ?, ?, ?, ?, ?)",
        insert_values(row),
    )
    if query is None:
        qWarning(f"Bookmarks: failed to insert {row.title}")
        return -1
    return int(query.lastInsertId())


def reparent(row_id: int, parent_id: int) -> bool:
    statement = "UPDATE bookmarks SET parent_id = ? WHERE id = ?"
    return sql.run(statement, (sql.id_or_null(parent_id), row_id)) is not None


def remove_subtree(row_id: int) -> bool:
    return sql.run(REMOVE_SUBTREE_STATEMENT, (row_id,)) is not None
