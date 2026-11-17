import sys

from PySide6.QtCore import QLoggingCategory, QMessageLogContext, QtMsgType, qInstallMessageHandler

SHOWN_CATEGORIES = ("kondor.extensions", "kondor.krunner")
# The QML loader thread logs through this handler and deadlocks on the GIL: https://github.com/lukasborges/kondor/issues/396
LOADER_THREAD_LOGGING_RULES = "qt.qml.propertyCache*=false"
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
    QLoggingCategory.setFilterRules(LOADER_THREAD_LOGGING_RULES)
    qInstallMessageHandler(print_to_standard_error)
