from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.site.identity.profileidentity import ProfileIdentity

PAGE = QUrl("https://responsive.example/")
OTHER = QUrl("https://other.example/")


@pytest.fixture
def tab(qapp: object, isolated_profile: object) -> Iterator[Tab]:
    created = Tab(ProfileManager.instance().defaultProfile())
    created.setUrl(PAGE)
    yield created
    created.responsive.release()
    created.deleteLater()


def agent_of(tab: Tab, host: str) -> str:
    identity = ProfileIdentity.of(ProfileManager.instance().defaultProfile())
    assert identity is not None
    return identity.agent_for(host)


def test_new_tab_is_not_in_responsive_mode(tab: Tab) -> None:
    assert not tab.responsive.isActive


def test_choosing_a_phone_sets_its_size_and_agent_and_reloads(tab: Tab, qtbot: QtBot) -> None:
    tab.responsive.setActive(True)
    with qtbot.waitSignal(tab.reloadRequested, timeout=500):
        tab.responsive.selectDevice("iphone15")
    assert (tab.responsive.width, tab.responsive.height) == (393, 852)
    assert "iPhone" in agent_of(tab, "responsive.example")


def test_turning_the_mode_off_restores_the_agent_and_reloads(tab: Tab, qtbot: QtBot) -> None:
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("pixel8")
    with qtbot.waitSignal(tab.reloadRequested, timeout=500):
        tab.responsive.setActive(False)
    assert agent_of(tab, "responsive.example") == ""


def test_editing_the_size_switches_to_responsive(tab: Tab) -> None:
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("iphone15")
    tab.responsive.setSize(500, 600)
    assert tab.responsive.device == "responsive"
    assert agent_of(tab, "responsive.example") == ""


def test_rotate_swaps_width_and_height(tab: Tab) -> None:
    tab.responsive.selectDevice("iphone15")
    tab.responsive.rotate()
    assert (tab.responsive.width, tab.responsive.height) == (852, 393)
    assert tab.responsive.device == "iphone15"


def test_navigating_to_another_host_moves_the_agent(tab: Tab) -> None:
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("iphone15")
    tab.setUrl(OTHER)
    assert agent_of(tab, "responsive.example") == ""
    assert "iPhone" in agent_of(tab, "other.example")


def test_zoom_to_fit_is_on_by_default(tab: Tab) -> None:
    assert tab.responsive.zoomToFit


def test_private_tab_does_not_remember_the_device(qapp: object, isolated_profile: object) -> None:
    private = Tab(ProfileManager.instance().createPrivateProfile())
    private.responsive.selectDevice("ipadair")
    assert Tab(None).responsive.device != "ipadair"
    private.deleteLater()
