from PySide6.QtCore import QByteArray, QMimeData, QObject, QTimer, Slot
from PySide6.QtGui import QGuiApplication

SECRET_HINT_FORMAT = "x-kde-passwordManagerHint"
SECRET_HINT = b"secret"
CLEAR_AFTER_MS = 30 * 1000


class PasswordClipboard(QObject):
    def __init__(self, parent: QObject | None = None, clear_after_ms: int = CLEAR_AFTER_MS) -> None:
        super().__init__(parent)
        self._secret = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(clear_after_ms)
        self._timer.timeout.connect(self._clear_if_still_holding)

    def copy(self, secret: str) -> None:
        data = QMimeData()
        data.setText(secret)
        data.setData(SECRET_HINT_FORMAT, QByteArray(SECRET_HINT))
        QGuiApplication.clipboard().setMimeData(data)
        self._secret = secret
        self._timer.start()

    def copy_text(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)

    @Slot()
    def _clear_if_still_holding(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if self._secret and clipboard.text() == self._secret:
            clipboard.clear()
        self._secret = ""
