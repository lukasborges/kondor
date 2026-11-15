import pytest
from PySide6.QtGui import QGuiApplication

from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.core.settings.settingsoptions import STORED_OPTIONS

pytestmark = pytest.mark.usefixtures("qapp")


def test_copies_the_address_as_plain_text(remote_control: RemoteControl) -> None:
    remote_control.set_port(9333)

    remote_control.copyAddress()

    assert QGuiApplication.clipboard().text() == "http://127.0.0.1:9333"


def test_has_no_address_while_inactive(remote_control: RemoteControl) -> None:
    assert remote_control.property("active") is False
    assert remote_control.property("address") == ""
    assert remote_control.property("port") == 0


def test_exposes_the_address_while_active(remote_control: RemoteControl) -> None:
    remote_control.set_port(9333)

    assert remote_control.property("active") is True
    assert remote_control.property("address") == "http://127.0.0.1:9333"


def test_settings_are_stored_under_the_remote_control_group() -> None:
    keys = {option.name: option.key for option in STORED_OPTIONS}

    assert keys["remoteControlEnabled"] == "RemoteControl/Enabled"
    assert keys["remoteControlPort"] == "RemoteControl/Port"
