import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, Qt, QUrl, Signal, Slot

from kondor.passwords.csvimport.importtypes import Result
from kondor.passwords.csvimport.passwordimport import parse
from kondor.passwords.csvimport.passwordimportfile import read_import_file, zero
from kondor.passwords.csvimport.passwordimportplan import SavedLogins, summarize_import
from kondor.passwords.importing.importinfo import (
    ImportInfo,
    import_error_name,
    import_failure,
    import_result,
)
from kondor.passwords.importing.pendingimport import PendingImport

SavedLoginsSource = Callable[[], SavedLogins | None]
WALLET_UNAVAILABLE = "walletUnavailable"


@dataclass
class ParsedImport:
    error: str = ""
    parsed: Result = field(default_factory=Result)


def read_and_parse(file: QUrl) -> ParsedImport:
    source = read_import_file(file)
    if source.error:
        return ParsedImport(source.error)
    parsed = ParsedImport(parsed=parse(source.data))
    zero(source.data)
    return parsed


class ImportPreparation(QObject):
    prepared = Signal("QVariantMap")
    runningChanged = Signal()
    _parsed = Signal(int, object)

    def __init__(self, saved_logins: SavedLoginsSource, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._saved_logins = saved_logins
        self._file = QUrl()
        self._pending = PendingImport()
        self._last_job = 0
        self._running_job: int | None = None
        self._parsed.connect(self._finish, Qt.ConnectionType.QueuedConnection)

    def start(self, file: QUrl) -> None:
        self._pending = PendingImport()
        self._file = QUrl(file)
        self._last_job += 1
        self._running_job = self._last_job
        job = (self._last_job, QUrl(file))
        threading.Thread(target=self._parse, args=job, daemon=True).start()
        self.runningChanged.emit()

    def cancel(self) -> None:
        self._pending = PendingImport()
        if not self.is_running():
            return
        self._running_job = None
        self.runningChanged.emit()

    def is_running(self) -> bool:
        return self._running_job is not None

    def take_pending(self) -> PendingImport:
        pending, self._pending = self._pending, PendingImport()
        return pending

    def _parse(self, job: int, file: QUrl) -> None:
        self._parsed.emit(job, read_and_parse(file))

    @Slot(int, object)
    def _finish(self, job: int, source: ParsedImport) -> None:
        if job != self._running_job:
            return
        self._running_job = None
        info = self._describe(source)
        self.runningChanged.emit()
        self.prepared.emit(info)

    def _describe(self, source: ParsedImport) -> ImportInfo:
        if source.error:
            return import_failure(self._file, source.error)
        error = import_error_name(source.parsed.error)
        if error:
            return import_failure(self._file, error)
        saved = self._saved_logins()
        if saved is None:
            return import_failure(self._file, WALLET_UNAVAILABLE)
        return self._keep_pending(source.parsed, saved)

    def _keep_pending(self, parsed: Result, saved: SavedLogins) -> ImportInfo:
        self._pending = PendingImport(parsed.logins, saved)
        return import_result(self._file, parsed, summarize_import(parsed.logins, saved))
