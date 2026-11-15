import os

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickWindow

ACTIVATION_VARIABLE = "XDG_ACTIVATION_TOKEN"


def raise_window(window: QObject, token: bytes) -> None:
    if not isinstance(window, QQuickWindow):
        return
    if token:
        os.environ[ACTIVATION_VARIABLE] = token.decode("utf-8")
    window.raise_()
    window.requestActivate()
