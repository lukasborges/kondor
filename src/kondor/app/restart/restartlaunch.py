from collections.abc import Mapping

from PySide6.QtCore import QProcess, QProcessEnvironment, qWarning

from kondor.app.remotecontrol import mcpcommand
from kondor.app.restart.launchenvironment import launch_environment

RESTORE_SESSION_FLAG = "--restore-session"


def restart_words(environment: Mapping[str, str]) -> list[str]:
    return [*mcpcommand.launch_words(environment), RESTORE_SESSION_FLAG]


def process_environment(environment: Mapping[str, str]) -> QProcessEnvironment:
    result = QProcessEnvironment()
    for name, value in environment.items():
        result.insert(name, value)
    return result


def start_detached(words: list[str], environment: Mapping[str, str]) -> bool:
    process = QProcess()
    process.setProgram(words[0])
    process.setArguments(words[1:])
    process.setProcessEnvironment(process_environment(environment))
    process.setUnixProcessParameters(QProcess.UnixProcessFlag.CloseFileDescriptors)
    return bool(process.startDetached())


def start_again() -> bool:
    environment = launch_environment()
    words = restart_words(environment)
    is_started = start_detached(words, environment)
    if not is_started:
        qWarning(f"Kondor: cannot restart with {' '.join(words)}")
    return is_started
