import sys

from PySide6.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

EXTENSIONS_CATEGORY = "kondor.extensions"
CHATTY_TYPES = (QtMsgType.QtDebugMsg, QtMsgType.QtInfoMsg)


def is_silenced(message_type: QtMsgType, category: str | None) -> bool:
    return message_type in CHATTY_TYPES and category != EXTENSIONS_CATEGORY


def print_to_standard_error(
    message_type: QtMsgType, context: QMessageLogContext, message: str
) -> None:
    if is_silenced(message_type, context.category):
        return
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def install_message_handler() -> None:
    qInstallMessageHandler(print_to_standard_error)
