import pytest

from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tabmodel import TabModel
from tests.app.remotecontrol.conftest import remote_control

__all__ = ["remote_control"]
pytestmark = pytest.mark.no_qt_log


def test_private_tab_is_refused_while_remote_control_is_on(
    model: TabModel, remote_control: RemoteControl, monkeypatch: pytest.MonkeyPatch
) -> None:
    remote_control.set_port(9333)
    created: list[object] = []
    monkeypatch.setattr(ProfileManager.instance(), "createPrivateProfile", created.append)

    assert model.addTab(True) is None
    assert model.count == 0
    assert created == []


def test_tabs_of_a_private_model_are_refused_too(
    model: TabModel, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)
    model.privateTabs = True

    assert model.addTab() is None


def test_normal_tabs_still_open_while_remote_control_is_on(
    model: TabModel, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)

    assert model.addTab() is not None


def test_private_browsing_is_available_by_default(remote_control: RemoteControl) -> None:
    assert ProfileManager.instance().property("privateBrowsingAvailable") is True
