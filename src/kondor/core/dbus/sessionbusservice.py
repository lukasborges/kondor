from collections.abc import Callable
from typing import Any

from jeepney import new_error, new_method_return, new_signal
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import DBusConnection, open_dbus_connection
from jeepney.wrappers import DBusAddress
from PySide6.QtCore import QObject, QSocketNotifier, qInfo, qWarning

from kondor.core.dbus.buscall import (
    BusCall,
    BusError,
    BusReply,
    BusSignal,
    CallHandler,
    call_from_message,
    is_method_call,
)

DO_NOT_QUEUE = 4
PRIMARY_OWNER = 1
UNKNOWN_METHOD = "org.freedesktop.DBus.Error.UnknownMethod"
PEER_INTERFACE = "org.freedesktop.DBus.Peer"
ServiceName = str | Callable[[str], str]


def open_session_connection() -> DBusConnection | None:
    try:
        return open_dbus_connection(bus="SESSION")
    except (OSError, KeyError, RuntimeError) as error:
        qWarning(f"Kondor: cannot reach the session bus: {error}")
        return None


def owns_service_name(connection: DBusConnection, name: str) -> bool:
    reply = connection.send_and_get_reply(message_bus.RequestName(name, DO_NOT_QUEUE), timeout=5)
    return bool(reply.body and reply.body[0] == PRIMARY_OWNER)


def resolve_name(name: ServiceName, unique_name: str) -> str:
    return name(unique_name) if callable(name) else name


class SessionBusService(QObject):
    def __init__(self, handler: CallHandler, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._handler = handler
        self._connection: DBusConnection | None = None
        self._notifier: QSocketNotifier | None = None

    @property
    def is_running(self) -> bool:
        return self._connection is not None

    @property
    def unique_name(self) -> str:
        return str(self._connection.unique_name) if self._connection is not None else ""

    def start(self, name: ServiceName) -> bool:
        connection = open_session_connection()
        if connection is None:
            return False
        service_name = resolve_name(name, str(connection.unique_name))
        if not owns_service_name(connection, service_name):
            qInfo(f"Kondor: the bus name {service_name} is taken")
            connection.close()
            return False
        self._watch(connection)
        return True

    def _watch(self, connection: DBusConnection) -> None:
        self._connection = connection
        self._notifier = QSocketNotifier(connection.sock.fileno(), QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self._read_calls)

    def stop(self) -> None:
        if self._notifier is not None:
            self._notifier.setEnabled(False)
            self._notifier = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def emit_signal(self, signal: BusSignal) -> None:
        if self._connection is None:
            return
        address = DBusAddress(signal.path, interface=signal.interface)
        self._connection.send(new_signal(address, signal.member, signal.signature, signal.body))

    def _read_calls(self) -> None:
        while self._connection is not None:
            try:
                message = self._connection.receive(timeout=0)
            except TimeoutError:
                return
            except OSError:
                self.stop()
                return
            self._answer(message)

    def _answer(self, message: Any) -> None:
        if not is_method_call(message) or self._connection is None:
            return
        call = call_from_message(message)
        self._connection.send(self._reply_message(message, self._reply_to(call)))

    def _reply_to(self, call: BusCall) -> BusReply | BusError | None:
        if call.interface == PEER_INTERFACE and call.member == "Ping":
            return BusReply()
        try:
            return self._handler(call)
        except Exception as error:  # noqa: BLE001
            qWarning(f"Kondor: D-Bus call {call.member} failed: {error}")
            return None

    @staticmethod
    def _reply_message(message: Any, reply: BusReply | BusError | None) -> Any:
        if reply is None:
            return new_error(message, UNKNOWN_METHOD)
        if isinstance(reply, BusError):
            return new_error(message, reply.name)
        return new_method_return(message, reply.signature, reply.body)
