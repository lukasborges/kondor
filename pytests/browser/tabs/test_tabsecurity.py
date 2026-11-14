import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from pytests.browser.tabs.conftest import site

pytestmark = pytest.mark.no_qt_log

FAILED_URL = site("expired")


def accepted_error_tab(model: TabModel, failed_url: QUrl) -> Tab:
    tab = model.addTab()
    tab.security.setPendingCertificateError(failed_url, "Expired", True)
    tab.security.acceptCertificateError()
    return tab


def test_security_state_follows_scheme(model: TabModel) -> None:
    tab = model.addTab()
    states = {}
    for url in ("https://example.com/", "http://example.com/", "file:///etc/hosts", "about:blank"):
        tab.setUrl(QUrl(url))
        states[url] = tab.security.state
    assert list(states.values()) == ["secure", "insecure", "local", "local"]


def test_accepting_the_error_clears_it_and_answers_the_view(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab()
    tab.security.setPendingCertificateError(QUrl("https://expired.example/"), "Expired", True)
    assert tab.security.certificateErrorPending
    assert tab.security.certificateErrorOverridable
    assert tab.security.state == "error"
    with qtbot.waitSignal(tab.security.acceptCertificateErrorRequested, timeout=0):
        tab.security.acceptCertificateError()
    assert not tab.security.certificateErrorPending


def test_override_keeps_the_error_state_when_coming_back(model: TabModel) -> None:
    tab = accepted_error_tab(model, FAILED_URL)
    tab.setUrl(site("other"))
    assert tab.security.state == "secure"
    tab.setUrl(FAILED_URL)
    assert tab.security.state == "error"


def test_override_reaches_every_tab_of_the_same_profile(model: TabModel) -> None:
    tab = accepted_error_tab(model, FAILED_URL)
    same_profile = model.addTab(False, FAILED_URL)
    assert same_profile.profile is tab.profile
    assert same_profile.security.state == "error"


def test_private_tab_never_inherits_the_override(model: TabModel) -> None:
    tab = accepted_error_tab(model, FAILED_URL)
    private_tab = model.addTab(True, FAILED_URL)
    assert private_tab.profile is not tab.profile
    assert private_tab.security.state == "secure"


def test_reject_certificate_error_clears_the_pending_error(model: TabModel, qtbot: QtBot) -> None:
    tab = model.addTab()
    tab.security.setPendingCertificateError(QUrl("https://bad.example/"), "Bad certificate", True)
    with qtbot.waitSignal(tab.security.rejectCertificateErrorRequested, timeout=0):
        tab.security.rejectCertificateError()
    assert not tab.security.certificateErrorPending
