from typing import Any

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
from PySide6.QtNetwork import QLocalSocket

from kondor.app.crash.actionlog import ActionLog
from kondor.app.remotecontrol.connections.connection import Connection

NAME_ROLE = Qt.ItemDataRole.UserRole + 1
SINCE_ROLE = NAME_ROLE + 1
CAN_DISCONNECT_ROLE = NAME_ROLE + 2


class ConnectionModel(QAbstractListModel):
    countChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._connections: list[Connection] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._connections)

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            NAME_ROLE: QByteArray(b"name"),
            SINCE_ROLE: QByteArray(b"connectedSince"),
            CAN_DISCONNECT_ROLE: QByteArray(b"canDisconnect"),
        }

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._connections):
            return None
        connection = self._connections[index.row()]
        return {
            NAME_ROLE: connection.name,
            SINCE_ROLE: connection.since,
            CAN_DISCONNECT_ROLE: connection.is_session(),
        }.get(role)

    def size(self) -> int:
        return len(self._connections)

    def add(self, connection: Connection) -> None:
        position = len(self._connections)
        self.beginInsertRows(QModelIndex(), position, position)
        self._connections.append(connection)
        self.endInsertRows()
        ActionLog.instance().record(f"remote control client connected: {connection.kind()}")
        self.countChanged.emit()

    def remove(self, connection: Connection) -> None:
        if connection not in self._connections:
            return
        position = self._connections.index(connection)
        self.beginRemoveRows(QModelIndex(), position, position)
        del self._connections[position]
        self.endRemoveRows()
        ActionLog.instance().record(f"remote control client disconnected: {connection.kind()}")
        self.countChanged.emit()

    def find_automation(self) -> Connection | None:
        return next((item for item in self._connections if not item.is_session()), None)

    def first_name(self) -> str:
        return self._connections[0].name if self._connections else ""

    def session_ports(self) -> set[int]:
        return {port for item in self._connections for port in item.ports}

    @Slot(int)
    def disconnectAt(self, row: int) -> None:
        socket = self.socket_at(row)
        if socket is not None:
            socket.disconnectFromServer()

    def socket_at(self, row: int) -> QLocalSocket | None:
        return self._connections[row].socket if 0 <= row < len(self._connections) else None

    firstName = Property(str, first_name, notify=countChanged)
    count = Property(int, size, notify=countChanged)
