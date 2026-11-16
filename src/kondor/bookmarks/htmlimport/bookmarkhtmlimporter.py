from PySide6.QtCore import QUrl

from kondor.bookmarks.bookmarkrow import BookmarkRow
from kondor.bookmarks.htmlimport.bookmarkhtmlparser import ImportedBookmark, ParsedBookmarks
from kondor.bookmarks.storage.bookmarkfoldertree import first_free_position, insert_row
from kondor.bookmarks.storage.bookmarkqueries import special_folder_id
from kondor.core.database import sql

IMPORTED_FOLDER_TITLE = "Imported"


class TreeInserter:
    def __init__(self) -> None:
        self._positions: dict[int, int] = {}
        self.inserted_bookmarks = 0

    def insert_children(self, parent: ImportedBookmark, parent_id: int) -> None:
        for child in parent.children:
            self._insert(child, parent_id)

    def _insert(self, node: ImportedBookmark, parent_id: int) -> None:
        position = self._take_position(parent_id)
        row_id = insert_row(BookmarkRow(node.is_folder, node.title, node.url, parent_id, position))
        if row_id <= 0:
            return
        if node.is_folder:
            self.insert_children(node, row_id)
        else:
            self.inserted_bookmarks += 1

    def _take_position(self, parent_id: int) -> int:
        position = self._positions.get(parent_id, 0)
        self._positions[parent_id] = position + 1
        return position


def insert_imported_folder() -> int:
    toolbar_id = special_folder_id("toolbar")
    position = first_free_position(toolbar_id)
    return insert_row(BookmarkRow(True, IMPORTED_FOLDER_TITLE, QUrl(), toolbar_id, position))


def insert_all(parsed: ParsedBookmarks, inserter: TreeInserter) -> bool:
    imported_folder = insert_imported_folder()
    if imported_folder <= 0:
        return False
    inserter.insert_children(parsed.root, imported_folder)
    return inserter.inserted_bookmarks == parsed.bookmark_count


def import_bookmarks(parsed: ParsedBookmarks) -> int:
    if parsed.bookmark_count == 0:
        return 0
    inserter = TreeInserter()
    is_committed = sql.in_transaction(lambda: insert_all(parsed, inserter))
    return inserter.inserted_bookmarks if is_committed else 0
