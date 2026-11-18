import re
import sys
from collections.abc import Callable

from PySide6.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

from kondor.app.crash.actionlog import ActionLog

URL_PATTERN = re.compile(r"\w+://\S+")
RECORDED_TYPES = (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg)
IGNORED_CATEGORY = "js"
Handler = Callable[[QtMsgType, QMessageLogContext, str], None]


def without_urls(message: str) -> str:
    return URL_PATTERN.sub("<url>", message)


def should_record(kind: QtMsgType, category: str | None) -> bool:
    return kind in RECORDED_TYPES and category != IGNORED_CATEGORY


def print_message(message: str) -> None:
    print(message, file=sys.stderr)


def chained_handler(previous: Handler | None) -> Handler:
    def handle(kind: QtMsgType, context: QMessageLogContext, message: str) -> None:
        if should_record(kind, context.category):
            ActionLog.instance().record(f"Qt message: {without_urls(message)}")
        if previous is None:
            print_message(message)
        else:
            previous(kind, context, message)

    return handle


def record_qt_messages() -> None:
    previous = qInstallMessageHandler(None)
    qInstallMessageHandler(chained_handler(previous))
