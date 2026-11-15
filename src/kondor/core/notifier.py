import os

from PySide6.QtCore import QObject, QProcess, Slot
from PySide6.QtGui import QGuiApplication

GDBUS_PROGRAM = "gdbus"
NOTIFICATIONS_SERVICE = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
NOTIFY_METHOD = "org.freedesktop.Notifications.Notify"
APPLICATION_ICON = "kondor"
FLATPAK_ID_VARIABLE = "FLATPAK_ID"
NEW_NOTIFICATION_ID = "0"
NO_ACTIONS = "[]"
NO_HINTS = "{}"
EXPIRE_TIMEOUT_MS = "5000"


def application_icon(icon_name: str) -> str:
    app_icon = os.environ.get(FLATPAK_ID_VARIABLE, APPLICATION_ICON)
    uses_app_icon = icon_name in ("", APPLICATION_ICON)
    return app_icon if uses_app_icon else icon_name


def gdbus_arguments(title: str, body: str, icon: str) -> list[str]:
    target = ["call", "--session", "--dest", NOTIFICATIONS_SERVICE]
    method = ["--object-path", NOTIFICATIONS_PATH, "--method", NOTIFY_METHOD]
    name = QGuiApplication.applicationDisplayName()
    notification = [name, NEW_NOTIFICATION_ID, icon, title, body]
    return target + method + notification + [NO_ACTIONS, NO_HINTS, EXPIRE_TIMEOUT_MS]


def send_notification(title: str, body: str, icon: str) -> None:
    QProcess.startDetached(GDBUS_PROGRAM, gdbus_arguments(title, body, icon))


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
        send_notification(title, body, icon)
