from collections.abc import Iterator

import pytest
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from pytestqt.qtbot import QtBot

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


def bridge_for(tab: Tab) -> PasswordBridge:
    bridge = PasswordBridge()
    bridge.tab = tab
    return bridge


def test_generating_needs_an_open_wallet(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    bridge = bridge_for(Tab(None))
    assert bridge.can_generate_for(ORIGIN) is False
    open_store(wallet_store, qtbot)
    assert bridge.can_generate_for(ORIGIN) is True


def test_private_tab_generates_nothing(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    bridge = bridge_for(Tab(QQuickWebEngineProfile()))
    assert bridge.can_generate_for(ORIGIN) is False
    assert bridge.generate_password({}) == ""


def test_never_save_site_generates_nothing(wallet_store: PasswordStore, qtbot: QtBot) -> None:
    open_store(wallet_store, qtbot)
    Settings.instance().setProperty(NEVER_SAVE_SITES, [ORIGIN])
    assert bridge_for(Tab(None)).can_generate_for(ORIGIN) is False


def test_generated_password_is_saved_without_a_prompt(
    wallet_store: PasswordStore, qtbot: QtBot
) -> None:
    open_store(wallet_store, qtbot)
    tab = Tab(None)
    bridge = bridge_for(tab)
    bridge.generated_password_filled(ORIGIN, "generated")
    bridge.form_submitted(ORIGIN, "ann", "generated")
    assert tab.passwords.prompt == ""
    assert wallet_store.password(ORIGIN, "ann") == "generated"


def test_edited_generated_password_shows_the_prompt(
    wallet_store: PasswordStore, qtbot: QtBot
) -> None:
    open_store(wallet_store, qtbot)
    tab = Tab(None)
    bridge = bridge_for(tab)
    bridge.generated_password_filled(ORIGIN, "generated")
    bridge.form_submitted(ORIGIN, "ann", "edited")
    assert tab.passwords.prompt == "save"
