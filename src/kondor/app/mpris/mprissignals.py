from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QTimer

from kondor.app.mpris.mprisproperties import (
    MICROSECONDS,
    PLAYER_INTERFACE,
    Properties,
)
from kondor.core.dbus.buscall import BusSignal
from kondor.core.dbus.sessionbusservice import SessionBusService

OBJECT_PATH = "/org/mpris/MediaPlayer2"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


class PlayerSignals(QObject):
    def __init__(
        self,
        bus: SessionBusService,
        values: Callable[[], Properties],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._bus = bus
        self._values = values
        self._sent: Properties = {}
        self._is_flush_pending = False

    def remember_current_values(self) -> None:
        self._sent = self._values()

    def schedule_flush(self) -> None:
        if not self._is_flush_pending:
            self._is_flush_pending = True
            QTimer.singleShot(0, self.flush)

    def changed_values(self) -> Properties:
        values = self._values()
        sent, self._sent = self._sent, values
        return {n: v for n, v in values.items() if n != "Position" and sent.get(n) != v}

    def flush(self) -> None:
        self._is_flush_pending = False
        changed = self.changed_values()
        if changed:
            body: tuple[Any, ...] = (PLAYER_INTERFACE, changed, [])
            signal = BusSignal(
                OBJECT_PATH, PROPERTIES_INTERFACE, "PropertiesChanged", "sa{sv}as", body
            )
            self._bus.emit_signal(signal)

    def send_seeked(self, position_seconds: float) -> None:
        position = int(position_seconds * MICROSECONDS)
        self._bus.emit_signal(BusSignal(OBJECT_PATH, PLAYER_INTERFACE, "Seeked", "x", (position,)))
