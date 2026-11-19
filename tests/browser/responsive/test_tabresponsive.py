from collections.abc import Iterator

import pytest
import shiboken6
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
    if shiboken6.isValid(created):
        shiboken6.delete(created)


def agent_of_host(host: str) -> str:
    identity = ProfileIdentity.of(ProfileManager.instance().defaultProfile())
    assert identity is not None
    return identity.agent_for(host)


def agent_of(tab: Tab, host: str) -> str:
    return agent_of_host(host)


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


def test_destroying_a_tab_in_responsive_mode_restores_the_agent(tab: Tab) -> None:
    tab.responsive.setActive(True)
    tab.responsive.selectDevice("iphone15")
    shiboken6.delete(tab)
    assert agent_of_host("responsive.example") == ""


def test_dragging_does_not_repeat_the_size_until_it_changes(tab: Tab) -> None:
    changes: list[int] = []
    tab.responsive.sizeChanged.connect(lambda: changes.append(1))
    tab.responsive.setSize(500, 600)
    tab.responsive.setSize(500, 600)
    assert len(changes) == 1


def test_destroying_the_profile_before_the_tab_raises_nothing(
    qapp: object, isolated_profile: object
) -> None:
    profile = ProfileManager.instance().createPrivateProfile()
    private = Tab(profile)
    shiboken6.delete(profile)
    shiboken6.delete(private)


def test_committing_a_size_remembers_it(tab: Tab) -> None:
    tab.responsive.commitSize(555, 666)
    reopened = Tab(ProfileManager.instance().defaultProfile())
    assert (reopened.responsive.width, reopened.responsive.height) == (555, 666)  # noqa: PLR2004
