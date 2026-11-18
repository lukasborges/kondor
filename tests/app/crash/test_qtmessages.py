from PySide6.QtCore import QtMsgType

from kondor.app.crash.qtmessages import should_record, without_urls


def test_replacesUrlsInMessages() -> None:
    message = "Failed https://secret.example/a?b=1 and file:///home/me/x"
    assert without_urls(message) == "Failed <url> and <url>"


def test_recordsWarningsOutsideTheJsCategory() -> None:
    assert should_record(QtMsgType.QtWarningMsg, "default")


def test_ignoresJsCategoryAndDebugMessages() -> None:
    assert not should_record(QtMsgType.QtWarningMsg, "js")
    assert not should_record(QtMsgType.QtDebugMsg, "default")
