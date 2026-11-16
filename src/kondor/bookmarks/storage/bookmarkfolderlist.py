from PySide6.QtSql import QSqlQuery

from kondor.bookmarks.storage.bookmarkcolumns import integer_at, text_at
from kondor.bookmarks.storage.bookmarkqueries import Row, special_folder_id
from kondor.bookmarks.storage.rootfoldernames import display_title
from kondor.core.database import sql

SPECIAL_ROOTS = ("toolbar", "other")


def special_root_ids() -> list[int]:
    found = (special_folder_id(special) for special in SPECIAL_ROOTS)
    return [row_id for row_id in found if row_id > 0]


def root_folder_ids() -> list[int]:
    roots = special_root_ids()
    others = sql.ids(
        "SELECT id FROM bookmarks WHERE parent_id IS NULL AND special IS NULL ORDER BY position, id"
    )
    return roots + [row_id for row_id in others if row_id not in roots]


def folder_row(folder: QSqlQuery, depth: int) -> Row:
    return {
        "id": integer_at(folder, 0),
        "title": display_title(text_at(folder, 3), text_at(folder, 1)),
        "parentId": integer_at(folder, 2),
        "depth": depth,
    }


def child_folder_ids(folder_id: int) -> list[int]:
    return sql.ids(
        "SELECT id FROM bookmarks WHERE parent_id = ? AND is_folder = 1 ORDER BY position, id",
        (folder_id,),
    )


def append_subtree(folder_id: int, depth: int, rows: list[Row]) -> None:
    folder = sql.run(
        "SELECT id, title, COALESCE(parent_id, 0), COALESCE(special, '')"
        " FROM bookmarks WHERE id = ? AND is_folder = 1",
        (folder_id,),
    )
    if folder is None or not folder.next():
        return
    rows.append(folder_row(folder, depth))
    for child_id in child_folder_ids(folder_id):
        append_subtree(child_id, depth + 1, rows)


def folders() -> list[Row]:
    rows: list[Row] = []
    for root in root_folder_ids():
        append_subtree(root, 0, rows)
    return rows
