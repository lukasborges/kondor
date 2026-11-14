from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from pytestqt.qtbot import QtBot
from shiboken6 import delete

from kondor.browser.tabs.tab import Tab
from kondor.core.settings.settings import Settings
from kondor.passwords.bridge.passwordbridge import PasswordBridge
from kondor.passwords.passwordstore import PasswordStore

pytestmark = pytest.mark.no_qt_log

ORIGIN = "https://a.example"
NEVER_SAVE_SITES = "passwordNeverSaveSites"


@pytest.fixture(autouse=True)
def clean_never_save_sites() -> Iterator[None]:
    settings = Settings.instance()
    previous = settings.property(NEVER_SAVE_SITES)
    settings.setProperty(NEVER_SAVE_SITES, [])
    yield
    settings.setProperty(NEVER_SAVE_SITES, previous)


@pytest.fixture
def wallet_store(store: PasswordStore, monkeypatch: pytest.MonkeyPatch) -> PasswordStore:
    monkeypatch.setattr(PasswordStore, "_instance", store)
    return store


def open_store(store: PasswordStore, qtbot: QtBot) -> None:
    store.ensureOpen()
    qtbot.waitUntil(lambda: store.state != "opening")


def bridge_for(tab: Tab | None) -> PasswordBridge:
    bridge = PasswordBridge()
    bridge.tab = tab
    return bridge


def normal_tab() -> Tab:
    return Tab(None)


def private_tab() -> Tab:
    return Tab(QQuickWebEngineProfile())


def test_private_tab_gets_no_credentials_and_no_offer(
    wallet_store: PasswordStore, qtbot: QtBot
) -> None:
    open_store(wallet_store, qtbot)
    wallet_store.save(ORIGIN, "ann", "secret")
    tab = private_tab()
    bridge = bridge_for(tab)
    bridge.form_submitted(ORIGIN, "bob", "other")
    assert bridge.credentials_for(ORIGIN) == []
    assert tab.passwords.prompt == ""


def test_form_submission_offers_to_save(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    tab = normal_tab()
    bridge_for(tab).form_submitted(ORIGIN, "ann", "secret")
    assert tab.passwords.prompt == "save"
    assert tab.passwords.promptUsername == "ann"


def test_never_save_site_is_not_offered(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    Settings.instance().setProperty(NEVER_SAVE_SITES, [ORIGIN])
    tab = normal_tab()
    bridge_for(tab).form_submitted(ORIGIN, "ann", "secret")
    assert tab.passwords.prompt == ""


def test_already_saved_login_is_not_offered(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    wallet_store.save(ORIGIN, "ann", "secret")
    tab = normal_tab()
    bridge_for(tab).form_submitted(ORIGIN, "ann", "secret")
    assert tab.passwords.prompt == ""


def test_unavailable_wallet_shows_the_notice_once(
    wallet_store: PasswordStore, wallet: object, qtbot: QtBot
) -> None:
    wallet.can_open = False  # type: ignore[attr-defined]
    open_store(wallet_store, qtbot)
    first, second = normal_tab(), normal_tab()
    bridge_for(first).form_submitted(ORIGIN, "ann", "secret")
    bridge_for(second).form_submitted(ORIGIN, "ann", "secret")
    assert first.passwords.prompt == "walletUnavailable"
    assert second.passwords.prompt == ""


def test_fill_emits_the_saved_password(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    wallet_store.save(ORIGIN, "ann", "secret")
    tab = normal_tab()
    tab.setUrl(QUrl(ORIGIN))
    bridge = bridge_for(tab)
    with qtbot.waitSignal(bridge.pageApi().fillRequested, timeout=0) as signal:
        bridge.fill("ann")
    assert signal.args == [ORIGIN, "ann", "secret"]


def test_store_change_reaches_the_page(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    bridge = bridge_for(normal_tab())
    with qtbot.waitSignal(bridge.pageApi().credentialsChanged, timeout=0):
        wallet_store.changed.emit()


def test_destroyed_tab_is_forgotten(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    tab = normal_tab()
    bridge = bridge_for(tab)
    delete(tab)
    assert bridge.tab is None


def test_page_api_keeps_the_channel_names(wallet_store: PasswordStore) -> None:
    api = bridge_for(None).pageApi()
    meta = api.metaObject()
    methods = {meta.method(index).name().data().decode() for index in range(meta.methodCount())}
    assert {"formSubmitted", "credentialsFor", "credentialsChanged", "fillRequested"} <= methods
