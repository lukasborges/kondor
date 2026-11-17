import pytest
from PySide6.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

import kondor.app.startup.appstartup  # noqa: F401
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
    assert seen_messages[0][1] == "kondor.extensions"


def test_warning_message_keeps_the_extensions_category(seen_messages) -> None:
    extensionloader.log_warning("Extension warning")
    assert seen_messages[0][1] == "kondor.extensions"
