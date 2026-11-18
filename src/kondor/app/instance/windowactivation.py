import os

from PySide6.QtCore import QObject, Qt
from PySide6.QtQuick import QQuickWindow

ACTIVATION_VARIABLE = "XDG_ACTIVATION_TOKEN"


def export_activation_token(token: bytes) -> None:
    if token:
        os.environ[ACTIVATION_VARIABLE] = token.decode("utf-8")


def raise_window(window: QObject | None, token: bytes) -> None:
    if not isinstance(window, QQuickWindow):
        return
    export_activation_token(token)
    if window.windowStates() & Qt.WindowState.WindowMinimized:
        window.showNormal()
    window.raise_()
    window.requestActivate()
