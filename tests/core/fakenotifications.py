import json
import sys

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtDBus import QDBusArgument, QDBusConnection, QDBusMessage, QDBusVirtualObject

SERVICE = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
READY = "READY"
TAKEN = "TAKEN"
NOTIFICATION_ID = 1
INTROSPECTION = """<interface name="org.freedesktop.Notifications">
  <method name="Notify">
    <annotation value="QVariantMap" name="org.qtproject.QtDBus.QtTypeName.In6"/>
    <arg direction="out" type="u"/>
    <arg direction="in" type="s" name="app_name"/>
    <arg direction="in" type="u" name="replaces_id"/>
    <arg direction="in" type="s" name="app_icon"/>
    <arg direction="in" type="s" name="summary"/>
    <arg direction="in" type="s" name="body"/>
    <arg direction="in" type="as" name="actions"/>
    <arg direction="in" type="a{sv}" name="hints"/>
    <arg direction="in" type="i" name="timeout"/>
  </method>
</interface>
"""


def read_map(argument: QDBusArgument) -> dict[str, str]:
    entries = {}
    argument.beginMap()
    while not argument.atEnd():
        argument.beginMapEntry()
        key = argument.asVariant()
        entries[str(key)] = repr(argument.asVariant())
        argument.endMapEntry()
    argument.endMap()
    return entries


def plain(value: object) -> object:
    return read_map(value) if isinstance(value, QDBusArgument) else value


def report(message: QDBusMessage) -> None:
    arguments = [plain(value) for value in message.arguments()]
    print(json.dumps({"signature": message.signature(), "arguments": arguments}), flush=True)


class FakeNotifications(QDBusVirtualObject):
    def introspect(self, path: str) -> str:
        return INTROSPECTION

    def handleMessage(self, message: QDBusMessage, connection: QDBusConnection) -> bool:
        if message.member() != "Notify":
            return False
        report(message)
        connection.send(message.createReply([NOTIFICATION_ID]))
        QTimer.singleShot(0, QCoreApplication.quit)
        return True


def main() -> int:
    application = QCoreApplication(sys.argv)
    bus = QDBusConnection.sessionBus()
    server = FakeNotifications()
    bus.registerVirtualObject(PATH, server)
    if not bus.registerService(SERVICE):
        print(TAKEN, flush=True)
        return 1
    print(READY, flush=True)
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
