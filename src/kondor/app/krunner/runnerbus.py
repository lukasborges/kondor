from collections.abc import Callable
from typing import Any

from jeepney import HeaderFields, MessageType, new_error, new_method_return
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import DBusConnection, open_dbus_connection
from PySide6.QtCore import QObject, QSocketNotifier, qInfo, qWarning

SERVICE_NAME = "io.github.lukasborges.Kondor.KRunner"
OBJECT_PATH = "/KRunner"
INTERFACE = "org.kde.krunner1"
DO_NOT_QUEUE = 4
PRIMARY_OWNER = 1
UNKNOWN_METHOD = "org.freedesktop.DBus.Error.UnknownMethod"

Reply = tuple[str, tuple[Any, ...]]
Handler = Callable[[str, tuple[Any, ...]], Reply | None]


def is_runner_call(message: Any) -> bool:
    header = message.header
    fields = header.fields
    is_call = header.message_type == MessageType.method_call
    return bool(
        is_call
        and fields.get(HeaderFields.path) == OBJECT_PATH
        and fields.get(HeaderFields.interface) == INTERFACE
    )


def owns_service_name(connection: DBusConnection) -> bool:
    request = message_bus.RequestName(SERVICE_NAME, DO_NOT_QUEUE)
    reply = connection.send_and_get_reply(request, timeout=5)
    return bool(reply.body and reply.body[0] == PRIMARY_OWNER)


class RunnerBus(QObject):
    def __init__(self, handler: Handler, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._handler = handler
        self._connection: DBusConnection | None = None
        self._notifier: QSocketNotifier | None = None

    def start(self) -> bool:
        connection = self._open_connection()
        if connection is None:
            return False
        if not owns_service_name(connection):
            qInfo("Kondor: another instance answers KRunner")
            connection.close()
            return False
        self._watch(connection)
        return True

    @staticmethod
    def _open_connection() -> DBusConnection | None:
        try:
            return open_dbus_connection(bus="SESSION")
        except (OSError, KeyError, RuntimeError) as error:
            qWarning(f"Kondor: cannot reach the session bus for KRunner: {error}")
            return None

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
        if not is_runner_call(message) or self._connection is None:
            return
        member = message.header.fields.get(HeaderFields.member, "")
        self._connection.send(self._reply_message(message, self._reply_to(member, message)))

    def _reply_to(self, member: str, message: Any) -> Reply | None:
        try:
            return self._handler(member, tuple(message.body))
        except Exception as error:  # noqa: BLE001
            qWarning(f"Kondor: KRunner call {member} failed: {error}")
            return None

    @staticmethod
    def _reply_message(call: Any, reply: Reply | None) -> Any:
        if reply is None:
            return new_error(call, UNKNOWN_METHOD)
        return new_method_return(call, *reply)
