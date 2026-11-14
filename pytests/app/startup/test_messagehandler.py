import pytest
from PySide6.QtCore import QtMsgType

from kondor.app.startup.messagehandler import is_silenced


@pytest.mark.parametrize(
    ("message_type", "category", "expected"),
    [
        pytest.param(QtMsgType.QtDebugMsg, "default", True, id="debug is silenced"),
        pytest.param(QtMsgType.QtInfoMsg, "default", True, id="info is silenced"),
        pytest.param(QtMsgType.QtDebugMsg, "kondor.extensions", False, id="extension debug"),
        pytest.param(QtMsgType.QtWarningMsg, "default", False, id="warning is shown"),
        pytest.param(QtMsgType.QtDebugMsg, None, True, id="no category"),
    ],
)
def test_is_silenced(message_type: QtMsgType, category: str | None, expected: bool) -> None:
    assert is_silenced(message_type, category) is expected
