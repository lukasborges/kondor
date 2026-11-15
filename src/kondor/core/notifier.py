import os
import threading

from PySide6.QtCore import Q_ARG, QGenericArgumentHolder, QMetaObject, QObject, Qt, Slot
from PySide6.QtDBus import QDBusConnection, QDBusInterface
from PySide6.QtGui import QGuiApplication

NOTIFICATIONS_SERVICE = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
NOTIFY_METHOD = "Notify"
APPLICATION_ICON = "kondor"
FLATPAK_ID_VARIABLE = "FLATPAK_ID"
NEW_NOTIFICATION_ID = 0
EXPIRE_TIMEOUT_MS = 5000


def application_icon(icon_name: str) -> str:
    app_icon = os.environ.get(FLATPAK_ID_VARIABLE, APPLICATION_ICON)
    uses_app_icon = icon_name in ("", APPLICATION_ICON)
    return app_icon if uses_app_icon else icon_name


def notify_arguments(title: str, body: str, icon: str) -> list[QGenericArgumentHolder]:
    return [
        Q_ARG(str, QGuiApplication.applicationDisplayName()),
        Q_ARG("uint", NEW_NOTIFICATION_ID),
        Q_ARG(str, icon),
        Q_ARG(str, title),
        Q_ARG(str, body),
        Q_ARG("QStringList", []),
        Q_ARG("QVariantMap", {}),
        Q_ARG(int, EXPIRE_TIMEOUT_MS),
    ]


def notifications_interface() -> QDBusInterface:
    bus = QDBusConnection.sessionBus()
    return QDBusInterface(NOTIFICATIONS_SERVICE, NOTIFICATIONS_PATH, NOTIFICATIONS_SERVICE, bus)


def call_notify(notifications: QDBusInterface, arguments: list[QGenericArgumentHolder]) -> None:
    connection = Qt.ConnectionType.DirectConnection
    QMetaObject.invokeMethod(notifications, NOTIFY_METHOD, connection, *arguments)


def send_notification(title: str, body: str, icon: str) -> None:
    notifications = notifications_interface()
    if notifications.isValid():
        call_notify(notifications, notify_arguments(title, body, icon))


class Notifier(QObject):
    _instance: "Notifier | None" = None

    @classmethod
    def instance(cls) -> "Notifier":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str, str, str)
    def notify(self, title: str, body: str, iconName: str) -> None:  # noqa: N803
        icon = application_icon(iconName)
        threading.Thread(target=send_notification, args=(title, body, icon), daemon=True).start()
