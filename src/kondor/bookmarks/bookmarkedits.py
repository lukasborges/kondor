from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl

from kondor.bookmarks.bookmarkrow import BookmarkRow, is_supported_bookmark_url
from kondor.bookmarks.storage import bookmarkchecks, bookmarkfoldertree, bookmarkqueries
from kondor.core.database import sql


def updates_rows(statement: str, values: Sequence[object]) -> bool:
    query = sql.run(statement, values)
    return query is not None and query.numRowsAffected() > 0


def read_utf8_file(file_url: QUrl) -> str:
    try:
        return Path(file_url.toLocalFile()).read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""


def new_bookmark_row(url: QUrl, title: str, folder_id: int) -> BookmarkRow | None:
    if not is_supported_bookmark_url(url):
        return None
    parent_id = bookmarkchecks.folder_or_other_bookmarks(folder_id)
    if parent_id <= 0:
        return None
    name = title.strip() or url.toString()
    position = bookmarkfoldertree.first_free_position(parent_id)
    return BookmarkRow(False, name, url, parent_id, position)


def new_folder_row(title: str, parent_id: int) -> BookmarkRow | None:
    if parent_id > 0 and not bookmarkchecks.is_folder_id(parent_id):
        return None
    valid_parent_id = max(parent_id, 0)
    name = title.strip() or QCoreApplication.translate("BookmarkManager", "New Folder")
    position = bookmarkfoldertree.first_free_position(valid_parent_id)
    return BookmarkRow(True, name, QUrl(), valid_parent_id, position)


def rename_row(row_id: int, title: str) -> bool:
    name = title.strip()
    statement = "UPDATE bookmarks SET title = ? WHERE id = ?"
    return bool(name) and updates_rows(statement, (name, row_id))


def set_row_url(row_id: int, url: QUrl) -> bool:
    statement = "UPDATE bookmarks SET url = ? WHERE id = ? AND is_folder = 0"
    return is_supported_bookmark_url(url) and updates_rows(statement, (url.toString(), row_id))


def move_row(row_id: int, new_parent_id: int, new_position: int) -> bool:
    item = bookmarkqueries.bookmark(row_id)
    parent_id = max(new_parent_id, 0)
    if not bookmarkchecks.can_move(item, parent_id):
        return False
    if not bookmarkfoldertree.reparent(row_id, parent_id):
        return False
    bookmarkfoldertree.renumber(parent_id, row_id, new_position)
    if item["parentId"] != parent_id:
        bookmarkfoldertree.renumber(item["parentId"], -1, 0)
    return True


def remove_row(row_id: int) -> bool:
    item = bookmarkqueries.bookmark(row_id)
    if not item or bookmarkchecks.is_special_row(item):
        return False
    if not bookmarkfoldertree.remove_subtree(row_id):
        return False
    bookmarkfoldertree.renumber(item["parentId"], -1, 0)
    return True
