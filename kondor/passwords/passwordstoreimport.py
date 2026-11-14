from PySide6.QtCore import QFile, QObject, QUrl, Signal, Slot

from kondor.passwords.csvimport.passwordimportplan import SavedLogins
from kondor.passwords.importing.importcommit import ImportCommit
from kondor.passwords.importing.importinfo import ImportInfo, import_failure
from kondor.passwords.importing.importoutcome import ImportOutcome
from kondor.passwords.importing.importpreparation import WALLET_UNAVAILABLE, ImportPreparation
from kondor.passwords.wallet.walletsession import WalletSession


def move_to_trash(file: QUrl) -> bool:
    return file.isLocalFile() and bool(QFile.moveToTrash(file.toLocalFile()))


class PasswordStoreImport(QObject):
    importPreparingChanged = Signal()
    importRunningChanged = Signal()
    importDoneChanged = Signal()
    importTotalChanged = Signal()
    importPrepared = Signal("QVariantMap")
    importFinished = Signal(int)
    loginsChanged = Signal()

    def __init__(self, session: WalletSession, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._preparation = ImportPreparation(self._saved_logins, self)
        self._commit: ImportCommit | None = None
        self._outcome = ImportOutcome()
        self._file_name = ""
        self._preparation.runningChanged.connect(self.importPreparingChanged)
        self._preparation.prepared.connect(self.importPrepared)

    def is_preparing(self) -> bool:
        return self._preparation.is_running()

    def is_running(self) -> bool:
        return self._commit is not None

    def done(self) -> int:
        return self._commit.done() if self._commit is not None else 0

    def total(self) -> int:
        return self._commit.total() if self._commit is not None else 0

    def prepare(self, file: QUrl) -> None:
        if self.is_running():
            return
        self._file_name = file.fileName()
        if self._session.open_folder() is not None:
            self._preparation.start(file)
        else:
            self.importPrepared.emit(import_failure(file, WALLET_UNAVAILABLE))

    def commit(self, replace_conflicts: bool) -> None:
        if self.is_running():
            return
        pending = self._preparation.take_pending()
        pending.replace_conflicts = replace_conflicts
        self._commit = ImportCommit(pending, self._write, self)
        self._commit.progressed.connect(self.importDoneChanged)
        self._commit.finished.connect(self._finish_commit)
        self._emit_progress_changed()
        self._commit.start()

    def cancel(self) -> None:
        self._preparation.cancel()
        self._preparation.take_pending()

    def set_page_open(self, is_open: bool) -> None:
        self._outcome.set_page_open(is_open)

    def take_result(self) -> ImportInfo:
        return self._outcome.take()

    def claim_notification(self) -> ImportInfo:
        return self._outcome.claim_notification()

    def _saved_logins(self) -> SavedLogins | None:
        folder = self._session.open_folder()
        return None if folder is None else folder.all_logins()

    def _write(self, origin: str, logins: dict[str, str]) -> bool:
        folder = self._session.open_folder()
        return folder is not None and folder.write_logins(origin, logins)

    def _emit_progress_changed(self) -> None:
        self.importRunningChanged.emit()
        self.importDoneChanged.emit()
        self.importTotalChanged.emit()

    @Slot(int)
    def _finish_commit(self, written: int) -> None:
        if self._commit is not None:
            self._commit.deleteLater()
        self._commit = None
        self.loginsChanged.emit()
        self._outcome.record(written, self._file_name)
        self._emit_progress_changed()
        self.importFinished.emit(written)
