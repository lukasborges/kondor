from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from kondor.passwords.csvimport.importtypes import Login
from kondor.passwords.csvimport.passwordimportplan import merge_logins
from kondor.passwords.importing.pendingimport import PendingImport

Writer = Callable[[str, dict[str, str]], bool]
FAILED = -1


def group_by_origin(logins: list[Login]) -> dict[str, list[Login]]:
    by_origin: dict[str, list[Login]] = {}
    for login in logins:
        by_origin.setdefault(login.origin, []).append(login)
    return by_origin


class ImportCommit(QObject):
    progressed = Signal()
    finished = Signal(int)

    def __init__(
        self, pending: PendingImport, write: Writer, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._by_origin = group_by_origin(pending.logins)
        self._origins = sorted(self._by_origin)
        self._saved = pending.saved
        self._is_replacing_conflicts = pending.replace_conflicts
        self._write = write
        self._done = 0
        self._written = 0

    def start(self) -> None:
        self._schedule_next()

    def total(self) -> int:
        return len(self._origins)

    def done(self) -> int:
        return self._done

    def _schedule_next(self) -> None:
        QTimer.singleShot(0, self, self._write_next_origin)

    def _write_next_origin(self) -> None:
        if self._done == self.total():
            self.finished.emit(self._written)
            return
        changes = self._merge_origin(self._origins[self._done])
        if changes == FAILED:
            self.finished.emit(FAILED)
            return
        self._advance(changes)

    def _advance(self, changes: int) -> None:
        self._written += changes
        self._done += 1
        self.progressed.emit()
        self._schedule_next()

    def _merge_origin(self, origin: str) -> int:
        saved = dict(self._saved.get(origin, {}))
        changes = merge_logins(saved, self._by_origin[origin], self._is_replacing_conflicts)
        if changes == 0:
            return 0
        return changes if self._write(origin, saved) else FAILED
