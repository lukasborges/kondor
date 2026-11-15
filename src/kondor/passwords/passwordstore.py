from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from kondor.passwords import passwordorigin
from kondor.passwords.passwordclipboard import PasswordClipboard
from kondor.passwords.passwordstoreimport import PasswordStoreImport, move_to_trash
from kondor.passwords.wallet.kwalletservice import KWalletService
from kondor.passwords.wallet.walletlogins import WalletLogins
from kondor.passwords.wallet.walletservice import WalletService
from kondor.passwords.wallet.walletsession import WalletSession


class PasswordStore(QObject):
    _instance: "PasswordStore | None" = None

    stateChanged = Signal()
    changed = Signal()
    importPreparingChanged = Signal()
    importRunningChanged = Signal()
    importDoneChanged = Signal()
    importTotalChanged = Signal()
    importPrepared = Signal("QVariantMap")
    importFinished = Signal(int)

    def __init__(self, service: WalletService | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        wallet = service if service is not None else KWalletService()
        self._session = WalletSession(wallet, self)
        self._logins = WalletLogins(self._session)
        self._import = PasswordStoreImport(self._session, self)
        self._clipboard = PasswordClipboard(self)
        self._is_notice_shown = False
        self._forward_session_signals()
        self._forward_import_signals()

    @classmethod
    def instance(cls) -> "PasswordStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _forward_session_signals(self) -> None:
        self._session.stateChanged.connect(self.stateChanged)
        self._session.changed.connect(self.changed)

    def _forward_import_signals(self) -> None:
        source = self._import
        source.importPreparingChanged.connect(self.importPreparingChanged)
        source.importRunningChanged.connect(self.importRunningChanged)
        source.importDoneChanged.connect(self.importDoneChanged)
        source.importTotalChanged.connect(self.importTotalChanged)
        source.importPrepared.connect(self.importPrepared)
        source.importFinished.connect(self.importFinished)
        source.loginsChanged.connect(self._notify_logins_changed)

    def _state_name(self) -> str:
        return self._session.state().value

    def _entries(self) -> list[dict[str, str]]:
        return self._session.usernames.entries()

    state = Property(str, _state_name, notify=stateChanged)
    entries = Property("QVariantList", _entries, notify=changed)
    importPreparing = Property(bool, lambda self: self._import.is_preparing(),
                               notify=importPreparingChanged)
    importRunning = Property(bool, lambda self: self._import.is_running(),
                             notify=importRunningChanged)
    importDone = Property(int, lambda self: self._import.done(), notify=importDoneChanged)
    importTotal = Property(int, lambda self: self._import.total(), notify=importTotalChanged)

    @Slot(QUrl, result=str)
    def originOf(self, url: QUrl) -> str:
        return passwordorigin.origin_of(url)

    @Slot(str, result=bool)
    def canSaveFor(self, origin: str) -> bool:
        return passwordorigin.can_save_for(origin)

    @Slot(str, result=str)
    def originFromInput(self, text: str) -> str:
        return passwordorigin.origin_from_input(text)

    @Slot(str, result=str)
    def hostOfOrigin(self, origin: str) -> str:
        return passwordorigin.host_of_origin(origin)

    def is_open(self) -> bool:
        return self._session.is_open()

    @Slot()
    def ensureOpen(self) -> None:
        self._session.ensure_open()

    @Slot()
    def retry(self) -> None:
        self._session.retry()

    def usernames(self, origin: str) -> list[str]:
        return self._session.usernames.usernames(origin)

    @Slot(str, str, result=str)
    def password(self, origin: str, username: str) -> str:
        return self._logins.password(origin, username)

    def credentials_for(self, origin: str) -> list[dict[str, str]]:
        return self._logins.credentials_for(origin)

    @Slot(str, str, result=bool)
    def contains(self, origin: str, username: str) -> bool:
        return username in self.usernames(origin)

    @Slot(str, str, str, result=bool)
    def save(self, origin: str, username: str, password: str) -> bool:
        is_saved = self._logins.save(origin, username, password)
        if is_saved:
            self._notify_logins_changed()
        return is_saved

    @Slot(str, str)
    def remove(self, origin: str, username: str) -> None:
        if self._logins.remove(origin, username):
            self._notify_logins_changed()

    @Slot(str, str)
    def copyPassword(self, origin: str, username: str) -> None:
        secret = self.password(origin, username)
        if secret:
            self._clipboard.copy(secret)

    def copy_text(self, text: str) -> None:
        self._clipboard.copy_text(text)

    @Slot(QUrl)
    def prepareImport(self, file: QUrl) -> None:
        self._import.prepare(file)

    @Slot(bool)
    def commitImport(self, replace_conflicts: bool) -> None:
        self._import.commit(replace_conflicts)

    @Slot()
    def cancelImport(self) -> None:
        self._import.cancel()

    @Slot(bool)
    def setImportPageOpen(self, is_open: bool) -> None:
        self._import.set_page_open(is_open)

    @Slot(result="QVariantMap")
    def takeImportResult(self) -> dict[str, str | int]:
        return self._import.take_result()

    @Slot(result="QVariantMap")
    def claimImportNotification(self) -> dict[str, str | int]:
        return self._import.claim_notification()

    @Slot(QUrl, result=bool)
    def moveImportFileToTrash(self, file: QUrl) -> bool:
        return move_to_trash(file)

    def unavailable_notice_shown(self) -> bool:
        return self._is_notice_shown

    def set_unavailable_notice_shown(self) -> None:
        self._is_notice_shown = True

    @Slot()
    def _notify_logins_changed(self) -> None:
        self._session.reload_usernames()
        self.changed.emit()
