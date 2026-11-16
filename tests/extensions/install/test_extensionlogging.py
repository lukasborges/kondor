import pytest
from PySide6.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

import kondor.app.startup.appstartup  # noqa: F401
from kondor.app.startup.messagehandler import is_silenced
from kondor.extensions.install import extensionloader


@pytest.fixture
def seen_messages():
    seen: list[tuple[QtMsgType, str | None, str]] = []

    def record(message_type: QtMsgType, context: QMessageLogContext, message: str) -> None:
        seen.append((message_type, context.category, message))

    previous = qInstallMessageHandler(record)
    yield seen
    qInstallMessageHandler(previous)


def test_info_message_keeps_the_extensions_category(seen_messages) -> None:
    extensionloader.log_info("Extension loaded")
    message_type, category, _ = seen_messages[0]
    assert category == "kondor.extensions"
    assert not is_silenced(message_type, category)


def test_warning_message_keeps_the_extensions_category(seen_messages) -> None:
    extensionloader.log_warning("Extension warning")
    assert seen_messages[0][1] == "kondor.extensions"
