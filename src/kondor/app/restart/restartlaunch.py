import os
from collections.abc import Mapping

from PySide6.QtCore import QProcess, qWarning

from kondor.app.remotecontrol import mcpcommand

RESTORE_SESSION_FLAG = "--restore-session"


def restart_words(environment: Mapping[str, str]) -> list[str]:
    return [*mcpcommand.launch_words(environment), RESTORE_SESSION_FLAG]


def start_detached(words: list[str]) -> bool:
    return bool(QProcess.startDetached(words[0], words[1:]))


def start_again() -> bool:
    words = restart_words(os.environ)
    is_started = start_detached(words)
    if not is_started:
        qWarning(f"Kondor: cannot restart with {' '.join(words)}")
    return is_started
