import sys

from PySide6.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

SHOWN_CATEGORIES = ("kondor.extensions", "kondor.krunner")
CHATTY_TYPES = (QtMsgType.QtDebugMsg, QtMsgType.QtInfoMsg)


def is_silenced(message_type: QtMsgType, category: str | None) -> bool:
    return message_type in CHATTY_TYPES and category not in SHOWN_CATEGORIES


def print_to_standard_error(
    message_type: QtMsgType, context: QMessageLogContext, message: str
) -> None:
    if is_silenced(message_type, context.category):
        return
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def install_message_handler() -> None:
    qInstallMessageHandler(print_to_standard_error)
