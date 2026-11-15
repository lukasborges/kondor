import os

import pytest
from PySide6.QtNetwork import QHostAddress, QTcpServer

from kondor.app.commandline.commandline import CommandLine
from kondor.app.remotecontrol import remotecontrolstartup as startup
from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.app.remotecontrol.remotecontrolenvironment import DEBUGGING_VARIABLE
from kondor.core.settings.settings import Settings

pytestmark = [pytest.mark.usefixtures("qapp", "remote_control")]


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    instance = Settings.instance()
    monkeypatch.setitem(instance._values, "remoteControlEnabled", False)
    monkeypatch.setitem(instance._values, "remoteControlPort", 9222)
    return instance


def free_port() -> int:
    server = QTcpServer()
    server.listen(QHostAddress.SpecialAddress.LocalHost, 0)
    port = server.serverPort()
    server.close()
    return port


def test_stays_inactive_by_default(settings: Settings, remote_control: RemoteControl) -> None:
    assert startup.start_remote_control(CommandLine()) is None

    assert not remote_control.is_active()
    assert remote_control.address_text() == ""


def test_setting_turns_it_on(
    settings: Settings, remote_control: RemoteControl, monkeypatch: pytest.MonkeyPatch
) -> None:
    port = free_port()
    monkeypatch.setitem(settings._values, "remoteControlEnabled", True)
    monkeypatch.setitem(settings._values, "remoteControlPort", port)

    startup.start_remote_control(CommandLine())

    assert remote_control.address_text() == f"http://127.0.0.1:{port}"
    assert os.environ[DEBUGGING_VARIABLE] == f"127.0.0.1:{port}"


def test_option_turns_it_on_without_the_setting(
    settings: Settings, remote_control: RemoteControl
) -> None:
    port = free_port()

    startup.start_remote_control(CommandLine(remote_control_port=str(port)))

    assert remote_control.port_number() == port
    assert remote_control.is_requested_on_command_line()
    assert settings.property("remoteControlEnabled") is False


@pytest.mark.usefixtures("settings")
def test_busy_port_leaves_it_off(
    remote_control: RemoteControl,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = QTcpServer()
    server.listen(QHostAddress.SpecialAddress.LocalHost, 0)
    port = server.serverPort()
    monkeypatch.setenv(DEBUGGING_VARIABLE, "9222")

    startup.start_remote_control(CommandLine(remote_control_port=str(port)))
    server.close()

    assert not remote_control.is_active()
    assert DEBUGGING_VARIABLE not in os.environ
    assert f"Kondor: port {port} is in use; remote control is off" in capsys.readouterr().err


def test_invalid_port_exits_with_status_two(capsys: pytest.CaptureFixture[str]) -> None:
    status = startup.check_option(CommandLine(remote_control_port="80"))

    assert status == startup.INVALID_ARGUMENT_STATUS
    assert "--remote-control needs a port from 1024 to 65535" in capsys.readouterr().err


def test_valid_port_has_no_error() -> None:
    assert startup.check_option(CommandLine(remote_control_port="9333")) is None
    assert startup.check_option(CommandLine()) is None


def test_private_with_remote_control_exits_with_status_two(
    remote_control: RemoteControl, capsys: pytest.CaptureFixture[str]
) -> None:
    remote_control.set_port(9333)

    status = startup.check_private(CommandLine(is_private=True))

    assert status == startup.INVALID_ARGUMENT_STATUS
    assert "private browsing is unavailable while remote control is on" in capsys.readouterr().err


def test_private_without_remote_control_is_fine(remote_control: RemoteControl) -> None:
    assert startup.check_private(CommandLine(is_private=True)) is None


def test_option_with_a_running_instance_exits_with_status_one() -> None:
    command_line = CommandLine(remote_control_port="9333")

    status = startup.check_running_instance(command_line, is_running=True)

    assert status == startup.ALREADY_RUNNING_STATUS


@pytest.mark.parametrize(
    ("command_line", "is_running"),
    [
        (CommandLine(remote_control_port="9333"), False),
        (CommandLine(remote_control_port="9333", new_instance=True), True),
        (CommandLine(), True),
    ],
)
def test_running_instance_is_fine_otherwise(command_line: CommandLine, is_running: bool) -> None:
    assert startup.check_running_instance(command_line, is_running) is None
