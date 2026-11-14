from kondor.bookmarks.storage import bookmarkfoldertree, bookmarkqueries
from kondor.bookmarks.storage.bookmarkqueries import Row


def is_folder_id(row_id: int) -> bool:
    return bool(bookmarkqueries.bookmark(row_id).get("isFolder", False))


def folder_or_other_bookmarks(folder_id: int) -> int:
    if folder_id > 0 and is_folder_id(folder_id):
        return folder_id
    return bookmarkqueries.special_folder_id("other")


def is_special_row(item: Row) -> bool:
    return bool(item.get("special", ""))


def can_move(item: Row, new_parent_id: int) -> bool:
    if not item or is_special_row(item):
        return False
    if new_parent_id > 0 and not is_folder_id(new_parent_id):
        return False
    is_folder = bool(item["isFolder"])
    return not (is_folder and bookmarkfoldertree.is_in_subtree(new_parent_id, int(item["id"])))
