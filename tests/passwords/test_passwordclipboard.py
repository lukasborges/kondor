from PySide6.QtGui import QGuiApplication
from pytestqt.qtbot import QtBot

from kondor.passwords.passwordclipboard import PasswordClipboard

SECRET_HINT = "x-kde-passwordManagerHint"
SHORT_CLEAR_MS = 20
WAIT_MS = 100


def test_copy_marks_password_secret(qapp: object) -> None:
    clipboard = PasswordClipboard()
    clipboard.copy("hunter2")
    data = QGuiApplication.clipboard().mimeData()
    assert data.text() == "hunter2"
    assert data.data(SECRET_HINT).data() == b"secret"


def test_copy_text_has_no_secret_hint(qapp: object) -> None:
    clipboard = PasswordClipboard()
    clipboard.copy_text("ana")
    assert not QGuiApplication.clipboard().mimeData().hasFormat(SECRET_HINT)


def test_copy_text_is_not_cleared(qtbot: QtBot) -> None:
    clipboard = PasswordClipboard(None, SHORT_CLEAR_MS)
    clipboard.copy("hunter2")
    clipboard.copy_text("ana")
    qtbot.wait(WAIT_MS)
    assert QGuiApplication.clipboard().text() == "ana"


def test_copy_is_cleared_after_the_timeout(qtbot: QtBot) -> None:
    clipboard = PasswordClipboard(None, SHORT_CLEAR_MS)
    clipboard.copy("hunter2")
    qtbot.waitUntil(lambda: QGuiApplication.clipboard().text() == "")
