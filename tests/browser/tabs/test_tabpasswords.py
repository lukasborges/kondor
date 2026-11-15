from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings

pytestmark = pytest.mark.no_qt_log

ORIGIN = "https://a.example"
NEVER_SAVE_SITES = "passwordNeverSaveSites"


@pytest.fixture(autouse=True)
def clean_never_save_sites(qapp: object) -> Iterator[None]:
    settings = Settings.instance()
    previous = settings.property(NEVER_SAVE_SITES)
    settings.setProperty(NEVER_SAVE_SITES, [])
    yield
    settings.setProperty(NEVER_SAVE_SITES, previous)


def test_private_tab_never_offers_to_save(model: TabModel) -> None:
    tab = model.addTab(True)
    tab.passwords.offer_save(ORIGIN, "ann", "secret")
    tab.passwords.show_wallet_notice()
    assert tab.passwords.prompt == ""


def test_never_save_adds_the_origin_once(model: TabModel) -> None:
    tab = model.addTab()
    for _ in range(2):
        tab.passwords.offer_save(ORIGIN, "ann", "secret")
        tab.passwords.neverSavePending()
    assert list(Settings.instance().property(NEVER_SAVE_SITES)) == [ORIGIN]
    assert tab.passwords.prompt == ""


def test_wallet_notice_replaces_the_save_prompt(model: TabModel) -> None:
    tab = model.addTab()
    tab.passwords.offer_save(ORIGIN, "ann", "secret")
    assert tab.passwords.prompt == "save"
    assert tab.passwords.promptHost == "a.example"
    tab.passwords.show_wallet_notice()
    assert tab.passwords.prompt == "walletUnavailable"
    assert tab.passwords.promptUsername == ""


def test_dismiss_clears_the_prompt(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab()
    tab.passwords.offer_save(ORIGIN, "ann", "secret")
    with qtbot.waitSignal(tab.passwords.promptChanged, timeout=0):
        tab.passwords.dismissPrompt()
    assert tab.passwords.prompt == ""
    assert tab.passwords.promptUsername == ""


def test_private_tab_does_not_copy(model: TabModel) -> None:
    tab = model.addTab(True)
    clipboard = QGuiApplication.clipboard()
    clipboard.setText("before")
    tab.passwords.copyUsername("ann")
    tab.passwords.copyPassword(ORIGIN, "ann")
    assert clipboard.text() == "before"


def test_host_follows_url(model: TabModel) -> None:
    tab = model.addTab()
    tab.passwords.update_usernames_for(QUrl("https://Example.org/login?x=1"))
    assert tab.passwords.host == "example.org"


def test_https_tab_without_logins_is_available(model: TabModel) -> None:
    tab = model.addTab()
    tab.passwords.update_usernames_for(QUrl(ORIGIN))
    assert tab.passwords.isAvailable


def test_non_web_tab_is_not_available(model: TabModel) -> None:
    tab = model.addTab()
    tab.passwords.update_usernames_for(QUrl("about:blank"))
    assert not tab.passwords.isAvailable


def test_private_tab_is_not_available(model: TabModel) -> None:
    tab = model.addTab(True)
    tab.passwords.update_usernames_for(QUrl(ORIGIN))
    assert not tab.passwords.isAvailable


def test_private_tab_has_no_matches(model: TabModel) -> None:
    tab = model.addTab(True)
    tab.passwords.update_usernames_for(QUrl(ORIGIN))
    assert tab.passwords.matches("a") == []


def test_fill_emits_the_saved_origin(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab()
    with qtbot.waitSignal(tab.passwords.fillRequested, timeout=0) as signal:
        tab.passwords.fill("https://other.example", "ann")
    assert signal.args == ["https://other.example", "ann"]
