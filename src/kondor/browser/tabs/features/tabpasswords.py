from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.browser.tabs.features.tabpasswordsuggestion import TabPasswordSuggestion
from kondor.core.settings.settings import Settings
from kondor.passwords import passwordorigin
from kondor.passwords.passwordsearch import matching_logins
from kondor.passwords.passwordstore import PasswordStore

NEVER_SAVE_SITES = "passwordNeverSaveSites"


class TabPasswords(QObject):
    promptChanged = Signal()
    usernamesChanged = Signal()
    availabilityChanged = Signal()
    walletStateChanged = Signal()
    fillRequested = Signal(str, str)

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._url = QUrl()
        self._prompt = ""
        self._origin = self._username = self._password = ""
        self._usernames: list[str] = []
        self._is_available = False
        self._suggestion = TabPasswordSuggestion(is_private, self)
        if not is_private:
            self._watch_store()

    def _watch_store(self) -> None:
        store = PasswordStore.instance()
        store.changed.connect(self._refresh_usernames)
        store.stateChanged.connect(self.walletStateChanged)

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
    suggestion = Property(TabPasswordSuggestion, lambda self: self._suggestion, constant=True)
    host = Property(str, _host, notify=usernamesChanged)
    usernames = Property("QStringList", lambda self: self._usernames, notify=usernamesChanged)

    def _is_wallet_unavailable(self) -> bool:
        return not self._is_private and PasswordStore.instance().state == "unavailable"

    isAvailable = Property(bool, lambda self: self._is_available, notify=availabilityChanged)
    isWalletUnavailable = Property(bool, _is_wallet_unavailable, notify=walletStateChanged)

    def update_usernames_for(self, url: QUrl) -> None:
        self._url = url
        self._suggestion.clear_field()
        names: list[str] = []
        if not self._is_private:
            names = PasswordStore.instance().usernames(passwordorigin.origin_of(url))
        assign_and_notify((self, "_usernames"), names, self.usernamesChanged)
        is_available = not self._is_private and bool(passwordorigin.origin_of(url))
        assign_and_notify((self, "_is_available"), is_available, self.availabilityChanged)

    @Slot(str, result="QVariantList")
    def matches(self, text: str) -> list[dict[str, object]]:
        if self._is_private:
            return []
        entries = PasswordStore.instance().entries
        return matching_logins(entries, text, passwordorigin.origin_of(self._url))

    @Slot()
    def openWallet(self) -> None:
        if not self._is_private:
            PasswordStore.instance().ensureOpen()

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

    @Slot(str, str)
    def fill(self, origin: str, username: str) -> None:
        if not self._is_private:
            self.fillRequested.emit(origin, username)

    @Slot(str)
    def copyUsername(self, username: str) -> None:
        if not self._is_private:
            PasswordStore.instance().copy_text(username)

    @Slot(str, str)
    def copyPassword(self, origin: str, username: str) -> None:
        if not self._is_private:
            PasswordStore.instance().copyPassword(origin, username)
