import pytest
from PySide6.QtNetwork import QHostAddress, QTcpServer

from kondor.app.remotecontrol.remotecontrolport import is_port_free, parse_port, requested_port

pytestmark = pytest.mark.usefixtures("qapp")
LOW_PORT = 1024
HIGH_PORT = 65535
PORT = 9333
OTHER_PORT = 9444


@pytest.mark.parametrize(
    ("text", "expected"), [("9333", PORT), ("1024", LOW_PORT), ("65535", HIGH_PORT)]
)
def test_parses_ports_in_range(text: str, expected: int) -> None:
    assert parse_port(text) == expected


@pytest.mark.parametrize("text", ["", "80", "1023", "65536", "abc", "-5", "92 22"])
def test_refuses_ports_out_of_range(text: str) -> None:
    assert parse_port(text) is None


def test_setting_off_decides_nothing() -> None:
    assert requested_port(None, False, 9222) is None


def test_setting_on_decides_its_port() -> None:
    assert requested_port(None, True, OTHER_PORT) == OTHER_PORT


def test_option_wins_over_setting_on() -> None:
    assert requested_port(PORT, True, OTHER_PORT) == PORT


def test_option_wins_over_setting_off() -> None:
    assert requested_port(PORT, False, 9222) == PORT


def test_busy_port_is_not_free() -> None:
    server = QTcpServer()
    assert server.listen(QHostAddress.SpecialAddress.LocalHost, 0)

    assert not is_port_free(server.serverPort())
    server.close()


def test_unused_port_is_free() -> None:
    server = QTcpServer()
    server.listen(QHostAddress.SpecialAddress.LocalHost, 0)
    port = server.serverPort()
    server.close()

    assert is_port_free(port)
