from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtSql import QSqlQuery

from kondor.core.database import sql
from kondor.history import historyentry, historysearch
from kondor.history.historyentry import HistoryEntry, Roles

REFRESH_DEBOUNCE_MS = 250
MAX_ENTRIES = 500
SELECT_ENTRIES = "SELECT id, url, title, visited_at FROM history"
FILTER_CLAUSE = " WHERE url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\'"
ORDER_CLAUSE = f" ORDER BY visited_at DESC, id DESC LIMIT {MAX_ENTRIES}"


def select_entries_statement(is_filtered: bool) -> str:
    return SELECT_ENTRIES + (FILTER_CLAUSE if is_filtered else "") + ORDER_CLAUSE


class HistoryModel(QAbstractListModel):
    Roles = Roles
    filterChanged = Signal()
    countChanged = Signal()
    activeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._filter = ""
        self._entries: list[HistoryEntry] = []
        self._is_active = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(REFRESH_DEBOUNCE_MS)
        self._refresh_timer.timeout.connect(self.refresh)

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._entries)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Roles.IdRole
    ) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        return historyentry.role_value(self._entries[index.row()], role)

    def roleNames(self) -> dict[int, QByteArray]:
        return historyentry.role_names()

    def filter_text(self) -> str:
        return self._filter

    def set_filter(self, text: str) -> None:
        if self._filter == text:
            return
        self._filter = text
        self.filterChanged.emit()
        self.refresh()

    def entry_count(self) -> int:
        return len(self._entries)

    def is_active(self) -> bool:
        return self._is_active

    def set_active(self, is_active: bool) -> None:
        if self._is_active == is_active:
            return
        self._is_active = is_active
        self.activeChanged.emit()
        if not is_active:
            return
        self._refresh_timer.stop()
        self.refresh()

    filter = Property(str, filter_text, set_filter, notify=filterChanged)
    count = Property(int, entry_count, notify=countChanged)
    active = Property(bool, is_active, set_active, notify=activeChanged)

    @Slot(int, result=str)
    def urlAt(self, index: int) -> str:
        if not 0 <= index < len(self._entries):
            return ""
        return str(self._entries[index].url.toString())

    def is_refresh_scheduled(self) -> bool:
        return bool(self._refresh_timer.isActive())

    def schedule_refresh(self) -> None:
        if self._is_active:
            self._refresh_timer.start()

    def refresh(self) -> None:
        entries = self.load_entries()
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()
        self.countChanged.emit()

    def query_entries(self) -> QSqlQuery | None:
        term = self._filter.strip()
        if not term:
            return sql.run(select_entries_statement(False))
        pattern = historysearch.like_pattern(term)
        return sql.run(select_entries_statement(True), (pattern, pattern))

    def load_entries(self) -> list[HistoryEntry]:
        entries = []
        rows = self.query_entries()
        while rows is not None and rows.next():
            entries.append(historyentry.entry_of(rows))
        return entries
