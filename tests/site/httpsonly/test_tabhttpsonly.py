from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.site.httpsonly.profilehttpsonly import ProfileHttpsOnly

pytestmark = pytest.mark.no_qt_log

ORIGINAL = QUrl("http://neverssl.example/page")


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


def upgraded_tab(model: TabModel, original: QUrl = ORIGINAL) -> tuple[Tab, ProfileHttpsOnly]:
    tab = model.addTab()
    state = ProfileHttpsOnly.of(tab.profile)
    assert state is not None
    tab.setUrl(state.record_upgrade(original))
    return tab, state


def test_tab_remembers_the_original_url(model: TabModel) -> None:
    tab, _ = upgraded_tab(model)
    assert tab.security.upgradedFrom == ORIGINAL
    assert not tab.security.httpsOnlyWarningPending


def test_finished_load_forgets_the_upgrade(model: TabModel) -> None:
    tab, _ = upgraded_tab(model)
    tab.security.finishUpgrade()
    assert tab.security.upgradedFrom.isEmpty()


def test_failed_load_shows_the_warning_as_not_secure(model: TabModel) -> None:
    tab, _ = upgraded_tab(model)
    assert tab.security.failUpgradeOf(tab.url)
    assert tab.security.httpsOnlyWarningPending
    assert tab.security.state == "insecure"


def test_failure_of_a_plain_https_load_is_not_a_warning(model: TabModel) -> None:
    tab = model.addTab()
    assert not tab.security.failUpgradeOf(QUrl("https://example.com/"))


def test_continue_allows_the_host_and_loads_the_original(model: TabModel, qtbot: QtBot) -> None:
    tab, state = upgraded_tab(model)
    tab.security.failUpgradeOf(tab.url)
    with qtbot.waitSignal(tab.security.continueToHttpRequested, timeout=0) as blocker:
        tab.security.continueToHttp()
    assert blocker.args == [ORIGINAL]
    assert "neverssl.example" in state.allowed_hosts()
    assert not tab.security.httpsOnlyWarningPending


def test_go_back_closes_the_warning(model: TabModel, qtbot: QtBot) -> None:
    tab, state = upgraded_tab(model, QUrl("http://leaving.example/"))
    tab.security.failUpgradeOf(tab.url)
    with qtbot.waitSignal(tab.security.leaveHttpsOnlyWarningRequested, timeout=0):
        tab.security.leaveHttpsOnlyWarning()
    assert not tab.security.httpsOnlyWarningPending
    assert "leaving.example" not in state.allowed_hosts()


def test_navigating_elsewhere_dismisses_the_warning(model: TabModel) -> None:
    tab, _ = upgraded_tab(model)
    tab.security.failUpgradeOf(tab.url)
    tab.navigateTo(QUrl("https://other.example/"))
    assert not tab.security.httpsOnlyWarningPending
