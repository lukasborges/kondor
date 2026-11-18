import faulthandler
from typing import TextIO

from kondor.app.crash.actionlog import ActionLog
from kondor.app.crash.crashfiles import CrashFiles, crash_directory
from kondor.app.crash.crashreporter import CrashReporter
from kondor.app.crash.qtmessages import record_qt_messages

_fault_files: list[TextIO] = []


def keep_fault_file(files: CrashFiles) -> None:
    fault_file = files.crash_log.open("w", encoding="utf-8")
    _fault_files.append(fault_file)
    faulthandler.enable(fault_file, all_threads=True)


def start_crash_recording(files: CrashFiles | None = None) -> CrashFiles:
    files = files or CrashFiles(crash_directory())
    files.directory.mkdir(parents=True, exist_ok=True)
    files.archive_previous_crash()
    keep_fault_file(files)
    ActionLog.instance().start(files.actions_log)
    CrashReporter.instance().offer(files)
    record_qt_messages()
    return files
