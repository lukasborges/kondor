from PySide6.QtCore import Property, QObject, Signal, Slot
from shiboken6 import isValid

from kondor.browser.tabs.tab import Tab
from kondor.core.settings.settings import Settings
from kondor.passwords.bridge.passwordpageapi import PasswordPageApi
from kondor.passwords.passwordorigin import can_save_for, origin_of
from kondor.passwords.passwordstore import PasswordStore


class PasswordBridge(QObject):
    tabChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab: Tab | None = None
        self._api = PasswordPageApi(self, self)
        PasswordStore.instance().changed.connect(self._api.credentialsChanged)

    def _get_tab(self) -> Tab | None:
        return self._tab if self._tab is not None and isValid(self._tab) else None

    def _set_tab(self, tab: Tab | None) -> None:
        if self._get_tab() is tab:
            return
        self._stop_watching_tab()
        self._tab = tab
        if tab is not None:
            tab.destroyed.connect(self._forget_tab)
        self.tabChanged.emit()

    def _stop_watching_tab(self) -> None:
        previous = self._get_tab()
        if previous is not None:
            previous.destroyed.disconnect(self._forget_tab)

    @Slot()
    def _forget_tab(self) -> None:
        self._tab = None
        self.tabChanged.emit()

    tab = Property(Tab, _get_tab, _set_tab, notify=tabChanged)

    @Slot(result=QObject)
    def pageApi(self) -> QObject:
        return self._api

    def _allowed_tab(self) -> Tab | None:
        tab = self._get_tab()
        return tab if tab is not None and not tab.isPrivate else None

    def _may_offer_save(self, origin: str, password: str) -> bool:
        if self._allowed_tab() is None or not password or not can_save_for(origin):
            return False
        settings = Settings.instance()
        never_sites = settings.property("passwordNeverSaveSites") or []
        return bool(settings.property("offerToSavePasswords")) and origin not in never_sites

    def _show_wallet_notice_once(self, tab: Tab) -> None:
        store = PasswordStore.instance()
        if store.unavailable_notice_shown():
            return
        store.set_unavailable_notice_shown()
        tab.passwords.show_wallet_notice()

    def _is_already_saved(self, origin: str, username: str, password: str) -> bool:
        store = PasswordStore.instance()
        return username in store.usernames(origin) and store.password(origin, username) == password

    def form_submitted(self, origin: str, username: str, password: str) -> None:
        tab = self._allowed_tab()
        if tab is None or not self._may_offer_save(origin, password):
            return
        store = PasswordStore.instance()
        store.ensureOpen()
        if store.state == "unavailable":
            self._show_wallet_notice_once(tab)
        elif store.is_open() and not self._is_already_saved(origin, username, password):
            tab.passwords.offer_save(origin, username, password)

    def credentials_for(self, origin: str) -> list[dict[str, str]]:
        if self._allowed_tab() is None or not origin:
            return []
        store = PasswordStore.instance()
        store.ensureOpen()
        return store.credentials_for(origin)

    @Slot(str)
    def fill(self, username: str) -> None:
        tab = self._allowed_tab()
        if tab is None:
            return
        origin = origin_of(tab.url)
        store = PasswordStore.instance()
        if origin and store.is_open():
            self._api.fillRequested.emit(origin, username, store.password(origin, username))
