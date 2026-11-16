from PySide6.QtCore import Property, QObject, QRectF, Signal, Slot
from shiboken6 import isValid

from kondor.browser.tabs.tab import Tab
from kondor.core.settings.settings import Settings
from kondor.passwords.bridge.passwordpageapi import PasswordPageApi
from kondor.passwords.passwordgenerator import generate_password, rules_from
from kondor.passwords.passwordorigin import can_save_for, origin_of
from kondor.passwords.passwordstore import PasswordStore


def number_in(values: dict[str, object], key: str) -> float:
    value = values.get(key)
    return float(value) if isinstance(value, int | float) else 0.0


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

    def _may_save_for(self, origin: str) -> bool:
        if self._allowed_tab() is None or not can_save_for(origin):
            return False
        settings = Settings.instance()
        never_sites = settings.property("passwordNeverSaveSites") or []
        return bool(settings.property("offerToSavePasswords")) and origin not in never_sites

    def _may_offer_save(self, origin: str, password: str) -> bool:
        return bool(password) and self._may_save_for(origin)

    def can_generate_for(self, origin: str) -> bool:
        return self._may_save_for(origin) and PasswordStore.instance().is_open()

    def _page_origin(self) -> str:
        tab = self._get_tab()
        return origin_of(tab.url) if tab is not None else ""

    def password_field_focused(self, field: dict[str, object]) -> None:
        tab = self._allowed_tab()
        if tab is None or not self.can_generate_for(self._page_origin()):
            return
        rect = QRectF(*(number_in(field, key) for key in ("x", "y", "width", "height")))
        tab.passwords.suggestion.show_field(
            str(field.get("kind", "")), bool(field.get("offer")), rect
        )

    def password_field_left(self) -> None:
        tab = self._allowed_tab()
        if tab is not None:
            tab.passwords.suggestion.clear_field()

    def generate_password(self, rules: dict[str, object]) -> str:
        if not self.can_generate_for(self._page_origin()):
            return ""
        return generate_password(rules_from(rules))

    def generated_password_filled(self, origin: str, password: str) -> None:
        tab = self._allowed_tab()
        if tab is not None and self.can_generate_for(origin):
            tab.passwords.suggestion.remember_generated(origin, password)

    @Slot()
    def requestGenerate(self) -> None:
        self._api.generateRequested.emit()

    def _show_wallet_notice_once(self, tab: Tab) -> None:
        store = PasswordStore.instance()
        if store.unavailable_notice_shown():
            return
        store.set_unavailable_notice_shown()
        tab.passwords.show_wallet_notice()

    def _is_already_saved(self, origin: str, username: str, password: str) -> bool:
        store = PasswordStore.instance()
        return username in store.usernames(origin) and store.password(origin, username) == password

    def _save_generated(self, tab: Tab, login: tuple[str, str, str]) -> None:
        if self._is_already_saved(*login):
            return
        if PasswordStore.instance().save(*login):
            tab.passwords.suggestion.announce_saved()

    def _offer_or_save(self, tab: Tab, login: tuple[str, str, str]) -> None:
        if tab.passwords.suggestion.take_generated(login[0], login[2]):
            self._save_generated(tab, login)
        elif not self._is_already_saved(*login):
            tab.passwords.offer_save(*login)

    def form_submitted(self, origin: str, username: str, password: str) -> None:
        tab = self._allowed_tab()
        if tab is None or not self._may_offer_save(origin, password):
            return
        store = PasswordStore.instance()
        store.ensureOpen()
        if store.state == "unavailable":
            self._show_wallet_notice_once(tab)
        elif store.is_open():
            self._offer_or_save(tab, (origin, username, password))

    def credentials_for(self, origin: str) -> list[dict[str, str]]:
        if self._allowed_tab() is None or not origin:
            return []
        store = PasswordStore.instance()
        store.ensureOpen()
        return store.credentials_for(origin)

    def _saved_password(self, saved_origin: str, username: str) -> str:
        store = PasswordStore.instance()
        return store.password(saved_origin, username) if store.is_open() else ""

    @Slot(str, str)
    def fill(self, saved_origin: str, username: str) -> None:
        tab = self._allowed_tab()
        if tab is None:
            return
        page_origin = origin_of(tab.url)
        password = self._saved_password(saved_origin, username)
        if page_origin and password:
            self._api.fillRequested.emit(page_origin, username, password)
