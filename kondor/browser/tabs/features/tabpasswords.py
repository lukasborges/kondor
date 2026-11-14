from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.core.settings.settings import Settings
from kondor.passwords import passwordorigin
from kondor.passwords.passwordstore import PasswordStore

NEVER_SAVE_SITES = "passwordNeverSaveSites"


class TabPasswords(QObject):
    promptChanged = Signal()
    usernamesChanged = Signal()
    fillRequested = Signal(str)

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._url = QUrl()
        self._prompt = ""
        self._origin = ""
        self._username = ""
        self._password = ""
        self._usernames: list[str] = []
        if not is_private:
            PasswordStore.instance().changed.connect(self._refresh_usernames)

    @Slot()
    def _refresh_usernames(self) -> None:
        self.update_usernames_for(self._url)

    def _prompt_host(self) -> str:
        return passwordorigin.host_of_origin(self._origin)

    def _host(self) -> str:
        return passwordorigin.host_of_origin(passwordorigin.origin_of(self._url))

    prompt = Property(str, lambda self: self._prompt, notify=promptChanged)
    promptUsername = Property(str, lambda self: self._username, notify=promptChanged)
    promptHost = Property(str, _prompt_host, notify=promptChanged)
    host = Property(str, _host, notify=usernamesChanged)
    usernames = Property("QStringList", lambda self: self._usernames, notify=usernamesChanged)

    def update_usernames_for(self, url: QUrl) -> None:
        self._url = url
        names: list[str] = []
        if not self._is_private:
            names = PasswordStore.instance().usernames(passwordorigin.origin_of(url))
        assign_and_notify((self, "_usernames"), names, self.usernamesChanged)

    def _clear_prompt(self) -> None:
        self._password = self._origin = self._username = ""
        assign_and_notify((self, "_prompt"), "", self.promptChanged)

    def _show_prompt(self, prompt: str) -> None:
        self._prompt = prompt
        self.promptChanged.emit()

    def offer_save(self, origin: str, username: str, password: str) -> None:
        if self._is_private:
            return
        self._origin, self._username, self._password = origin, username, password
        self._show_prompt("save")

    def show_wallet_notice(self) -> None:
        if self._is_private:
            return
        self._password = self._username = self._origin = ""
        self._show_prompt("walletUnavailable")

    @Slot()
    def savePending(self) -> None:
        if self._is_private or self._prompt != "save":
            return
        PasswordStore.instance().save(self._origin, self._username, self._password)
        self._clear_prompt()

    def _add_origin_to_never_save_sites(self) -> None:
        settings = Settings.instance()
        sites = list(settings.property(NEVER_SAVE_SITES) or [])
        if self._origin in sites:
            return
        settings.setProperty(NEVER_SAVE_SITES, [*sites, self._origin])

    @Slot()
    def neverSavePending(self) -> None:
        if self._prompt != "save":
            return
        self._add_origin_to_never_save_sites()
        self._clear_prompt()

    @Slot()
    def dismissPrompt(self) -> None:
        self._clear_prompt()

    @Slot(str)
    def fill(self, username: str) -> None:
        if not self._is_private:
            self.fillRequested.emit(username)

    @Slot(str)
    def copyUsername(self, username: str) -> None:
        if not self._is_private:
            PasswordStore.instance().copy_text(username)

    @Slot(str)
    def copyPassword(self, username: str) -> None:
        if self._is_private:
            return
        origin = passwordorigin.origin_of(self._url)
        PasswordStore.instance().copyPassword(origin, username)
