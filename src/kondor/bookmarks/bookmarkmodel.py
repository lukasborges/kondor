from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from PySide6.QtCore import Property as QtProperty
from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtSql import QSqlQuery

from kondor.bookmarks.storage.bookmarkcolumns import flag_at, integer_at, text_at
from kondor.bookmarks.storage.bookmarkqueries import like_pattern
from kondor.core.database import sql

NO_FOLDER = -1


@dataclass(frozen=True)
class Entry:
    id: int
    parent_id: int
    title: str
    url: str
    is_folder: bool


def read_entry(query: QSqlQuery) -> Entry:
    url = QUrl(text_at(query, 3)).toString()
    return Entry(
        integer_at(query, 0), integer_at(query, 1), text_at(query, 2), url, flag_at(query, 4)
    )


class BookmarkModel(QAbstractListModel):
    class Roles(IntEnum):
        IdRole = Qt.ItemDataRole.UserRole + 1
        ParentIdRole = IdRole + 1
        TitleRole = ParentIdRole + 1
        UrlRole = TitleRole + 1
        IsFolderRole = UrlRole + 1

    ROLE_FIELDS: dict[int, tuple[str, str]] = {
        Roles.IdRole: ("id", "id"),
        Roles.ParentIdRole: ("parentId", "parent_id"),
        Roles.TitleRole: ("title", "title"),
        Roles.UrlRole: ("url", "url"),
        Roles.IsFolderRole: ("isFolder", "is_folder"),
    }

    folderIdChanged = Signal()
    filterChanged = Signal()
    countChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._folder_id = NO_FOLDER
        self._filter = ""
        self._entries: list[Entry] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not self._has_row(index.row()) or role not in self.ROLE_FIELDS:
            return None
        return getattr(self._entries[index.row()], self.ROLE_FIELDS[role][1])

    def roleNames(self) -> dict[int, QByteArray]:
        return {role: QByteArray(names[0].encode()) for role, names in self.ROLE_FIELDS.items()}

    def folder_id(self) -> int:
        return self._folder_id

    def set_folder_id(self, folder_id: int) -> None:
        if self._folder_id == folder_id:
            return
        self._folder_id = folder_id
        self.folderIdChanged.emit()
        self.refresh()

    def filter_text(self) -> str:
        return self._filter

    def set_filter(self, filter_text: str) -> None:
        if self._filter == filter_text:
            return
        self._filter = filter_text
        self.filterChanged.emit()
        self.refresh()

    def count_rows(self) -> int:
        return len(self._entries)

    folderId = QtProperty("qint64", folder_id, set_folder_id, notify=folderIdChanged)
    filter = QtProperty(str, filter_text, set_filter, notify=filterChanged)
    count = QtProperty(int, count_rows, notify=countChanged)

    @Slot(int, result=str)
    def urlAt(self, row: int) -> str:
        return self._entries[row].url if self._has_row(row) else ""

    @Slot(int, result="qint64")
    def idAt(self, row: int) -> int:
        return self._entries[row].id if self._has_row(row) else -1

    @Slot(int, result=bool)
    def isFolderAt(self, row: int) -> bool:
        return self._has_row(row) and self._entries[row].is_folder

    @Slot("qint64", result=int)
    def rowOf(self, row_id: int) -> int:
        rows = (row for row, entry in enumerate(self._entries) if entry.id == row_id)
        return next(rows, -1)

    @Slot()
    def refresh(self) -> None:
        entries = self._load_entries()
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()
        self.countChanged.emit()

    def _has_row(self, row: int) -> bool:
        return 0 <= row < len(self._entries)

    def _search_term(self) -> str:
        return self._filter.strip()

    def _select_statement(self) -> str:
        statement = "SELECT id, parent_id, title, url, is_folder FROM bookmarks WHERE parent_id = ?"
        if self._search_term():
            statement += " AND (title LIKE ? ESCAPE '\\' OR url LIKE ? ESCAPE '\\')"
        return statement + " ORDER BY position, id"

    def _bind_values(self) -> tuple[object, ...]:
        term = self._search_term()
        if not term:
            return (self._folder_id,)
        pattern = like_pattern(term)
        return (self._folder_id, pattern, pattern)

    def _load_entries(self) -> list[Entry]:
        entries: list[Entry] = []
        if self._folder_id < 0:
            return entries
        query = sql.run(self._select_statement(), self._bind_values())
        while query is not None and query.next():
            entries.append(read_entry(query))
        return entries
