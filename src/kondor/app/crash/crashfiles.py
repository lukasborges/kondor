from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def crash_directory() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    return Path(base) / "crash"


@dataclass(frozen=True)
class CrashFiles:
    directory: Path

    @property
    def crash_log(self) -> Path:
        return self.directory / "crash.log"

    @property
    def actions_log(self) -> Path:
        return self.directory / "actions.log"

    @property
    def last_crash_log(self) -> Path:
        return self.directory / "last-crash.log"

    @property
    def last_actions_log(self) -> Path:
        return self.directory / "last-actions.log"

    def has_previous_crash(self) -> bool:
        return self.last_crash_log.is_file()

    def archive_previous_crash(self) -> None:
        if not self.crash_log.is_file() or self.crash_log.stat().st_size == 0:
            return
        self.crash_log.replace(self.last_crash_log)
        self.last_actions_log.unlink(missing_ok=True)
        if self.actions_log.is_file():
            self.actions_log.replace(self.last_actions_log)

    def read_previous_crash(self) -> str:
        return self.last_crash_log.read_text(encoding="utf-8", errors="replace").strip()

    def read_previous_actions(self) -> str:
        if not self.last_actions_log.is_file():
            return ""
        return self.last_actions_log.read_text(encoding="utf-8", errors="replace").strip()

    def discard_previous_crash(self) -> None:
        self.last_crash_log.unlink(missing_ok=True)
        self.last_actions_log.unlink(missing_ok=True)
