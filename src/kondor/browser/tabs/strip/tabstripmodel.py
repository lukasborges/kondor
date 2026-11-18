from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
    Signal,
    Slot,
)

from kondor.browser.tabs.groups.tabgroup import TabGroup
from kondor.browser.tabs.strip.striprow import LABEL, StripRole, StripRow, build_rows
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel

ROLE_NAMES = {
    StripRole.KIND: b"kind",
    StripRole.TAB: b"tab",
    StripRole.GROUP: b"group",
    StripRole.IS_HIDDEN: b"isHidden",
    StripRole.IS_PINNED: b"isPinned",
    StripRole.TAB_INDEX: b"tabIndex",
}


class TabStripModel(QAbstractListModel):
    sourceChanged = Signal()
    countChanged = Signal()
    revisionChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._source: TabModel | None = None
        self._rows: list[StripRow] = []
        self._revision = 0
        self._is_stale = False
        self._is_refreshing = False

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return 0 if parent is not None and parent.isValid() else len(self._rows)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        return self._rows[index.row()].value_for(role)

    def roleNames(self) -> dict[int, QByteArray]:
        return {role: QByteArray(name) for role, name in ROLE_NAMES.items()}

    def _get_source(self) -> TabModel | None:
        return self._source

    def _set_source(self, source: TabModel | None) -> None:
        if source is self._source:
            return
        self._source = source
        if source is not None:
            self._follow(source)
        self.refresh()
        self.sourceChanged.emit()

    def _follow(self, source: TabModel) -> None:
        for signal in (source.rowsInserted, source.rowsRemoved, source.rowsMoved):
            signal.connect(self.refresh)
        for signal in (source.modelReset, source.layoutChanged, source.groupsChanged):
            signal.connect(self.refresh)
        source.pinnedCountChanged.connect(self.refresh)

    source = Property(QObject, _get_source, _set_source, notify=sourceChanged)
    count = Property(int, lambda self: len(self._rows), notify=countChanged)
    revision = Property(int, lambda self: self._revision, notify=revisionChanged)

    @Slot()
    def refresh(self) -> None:
        self._is_stale = True
        if self._is_refreshing:
            return
        self._is_refreshing = True
        while self._is_stale:
            self._is_stale = False
            self._rebuild()
        self._is_refreshing = False

    def _rebuild(self) -> None:
        wanted = build_rows(self._source.all_tabs()) if self._source is not None else []
        before = len(self._rows)
        self._remove_vanished(wanted)
        self._arrange(wanted)
        self._update_values(wanted)
        if len(self._rows) != before:
            self.countChanged.emit()
        self._revision += 1
        self.revisionChanged.emit()

    def _remove_vanished(self, wanted: list[StripRow]) -> None:
        keys = {row.key for row in wanted}
        for position in reversed(range(len(self._rows))):
            if self._rows[position].key not in keys:
                self.beginRemoveRows(QModelIndex(), position, position)
                del self._rows[position]
                self.endRemoveRows()

    def _arrange(self, wanted: list[StripRow]) -> None:
        for position, row in enumerate(wanted):
            if position < len(self._rows) and self._rows[position].key == row.key:
                continue
            found = self._position_of(row.key)
            if found < 0:
                self._insert(position, row)
            else:
                self._move(found, position)

    def _position_of(self, key: tuple[str, object]) -> int:
        return next((i for i, row in enumerate(self._rows) if row.key == key), -1)

    def _insert(self, position: int, row: StripRow) -> None:
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.insert(position, row)
        self.endInsertRows()

    def _move(self, found: int, position: int) -> None:
        self.beginMoveRows(QModelIndex(), found, found, QModelIndex(), position)
        self._rows.insert(position, self._rows.pop(found))
        self.endMoveRows()

    def _update_values(self, wanted: list[StripRow]) -> None:
        for position, row in enumerate(wanted):
            if self._rows[position] == row:
                continue
            self._rows[position] = row
            changed = self.index(position, 0)
            self.dataChanged.emit(changed, changed)

    @Slot(int, result=bool)
    def isLabel(self, row: int) -> bool:
        return 0 <= row < len(self._rows) and self._rows[row].kind == LABEL

    @Slot(int, result=bool)
    def isHidden(self, row: int) -> bool:
        return 0 <= row < len(self._rows) and self._rows[row].is_hidden

    @Slot(int, result=TabGroup)
    def groupAt(self, row: int) -> TabGroup | None:
        return self._rows[row].group if 0 <= row < len(self._rows) else None

    @Slot(int, result=int)
    def tabIndexAt(self, row: int) -> int:
        if self._source is None or not 0 <= row < len(self._rows):
            return -1
        current = self._rows[row]
        if current.kind == LABEL and current.group is not None:
            return int(self._source.firstIndexOf(current.group))
        return int(self._source.indexOfTab(current.tab)) if current.tab is not None else -1

    @Slot(int, result=int)
    def rowOfTabIndex(self, tab_index: int) -> int:
        tab = self._source.tabAt(tab_index) if self._source is not None else None
        return self.rowOfTab(tab) if tab is not None else -1

    @Slot(Tab, result=int)
    def rowOfTab(self, tab: Tab) -> int:
        return next((i for i, row in enumerate(self._rows) if row.tab is tab), -1)

    @Slot(TabGroup, result=int)
    def rowOfLabel(self, group: TabGroup) -> int:
        return next((i for i, row in enumerate(self._rows) if self._is_label_of(row, group)), -1)

    def _is_label_of(self, row: StripRow, group: TabGroup) -> bool:
        return row.kind == LABEL and row.group is group
