from collections.abc import Iterator

import pytest
from jeepney import MatchRule, Message
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import DBusConnection, open_dbus_connection
from PySide6.QtCore import QProcess
from pytestqt.qtbot import QtBot

from kondor.core.dbus.buscall import BusCall, BusError, BusReply, BusSignal
from kondor.core.dbus.sessionbusservice import SessionBusService

SERVICE_NAME = "io.github.lukasborges.Kondor.TestBus"
OBJECT_PATH = "/Test"
INTERFACE = "io.github.lukasborges.Kondor.Test"


def handler(call: BusCall) -> BusReply | BusError | None:
    if call.member == "Echo":
        return BusReply("s", (f"{call.member}:{call.body[0]}",))
    return BusError("io.github.lukasborges.Kondor.Test.Failed") if call.member == "Fail" else None


@pytest.fixture
def bus(qapp: object) -> Iterator[SessionBusService]:
    service = SessionBusService(handler)
    assert service.start(SERVICE_NAME)
    yield service
    service.stop()


def gdbus(qtbot: QtBot, *arguments: str) -> tuple[int, str]:
    process = QProcess()
    process.start("gdbus", ["call", "--session", *arguments])
    qtbot.waitUntil(lambda: process.state() == QProcess.ProcessState.NotRunning, timeout=10000)
    output = (
        bytes(process.readAllStandardOutput()).decode()
        + bytes(process.readAllStandardError()).decode()
    )
    return process.exitCode(), output


def call(qtbot: QtBot, method: str) -> tuple[int, str]:
    return gdbus(
        qtbot,
        "--dest",
        SERVICE_NAME,
        "--object-path",
        OBJECT_PATH,
        "--method",
        f"{INTERFACE}.{method}",
        "kon",
    )


def test_start_owns_the_service_name(bus: SessionBusService, qtbot: QtBot) -> None:
    code, output = gdbus(
        qtbot,
        "--dest",
        "org.freedesktop.DBus",
        "--object-path",
        "/org/freedesktop/DBus",
        "--method",
        "org.freedesktop.DBus.NameHasOwner",
        SERVICE_NAME,
    )

    assert "true" in output, (code, output)


def test_second_service_does_not_start(bus: SessionBusService) -> None:
    second = SessionBusService(handler)

    assert second.start(SERVICE_NAME) is False


def test_name_can_be_built_from_the_unique_name(qapp: object) -> None:
    service = SessionBusService(handler)
    names: list[str] = []

    def build(unique_name: str) -> str:
        names.append(unique_name)
        return SERVICE_NAME + "Built"

    assert service.start(build)
    assert names == [service.unique_name]
    assert service.unique_name.startswith(":")
    service.stop()


def test_call_gets_the_handler_reply(bus: SessionBusService, qtbot: QtBot) -> None:
    code, output = call(qtbot, "Echo")

    assert "Echo:kon" in output, (code, output)


def test_handler_error_is_sent_back(bus: SessionBusService, qtbot: QtBot) -> None:
    code, output = call(qtbot, "Fail")

    assert "Test.Failed" in output, (code, output)


def test_unknown_method_gets_an_error(bus: SessionBusService, qtbot: QtBot) -> None:
    code, output = call(qtbot, "Nothing")

    assert "UnknownMethod" in output, (code, output)


def test_peer_ping_is_answered(bus: SessionBusService, qtbot: QtBot) -> None:
    code, output = gdbus(
        qtbot,
        "--dest",
        SERVICE_NAME,
        "--object-path",
        OBJECT_PATH,
        "--method",
        "org.freedesktop.DBus.Peer.Ping",
    )

    assert code == 0, output


def test_stop_releases_the_name(qapp: object) -> None:
    first = SessionBusService(handler)
    assert first.start(SERVICE_NAME)
    first.stop()
    second = SessionBusService(handler)

    assert second.start(SERVICE_NAME)
    second.stop()


def listener() -> DBusConnection:
    connection = open_dbus_connection(bus="SESSION")
    rule = MatchRule(type="signal", interface=INTERFACE, path=OBJECT_PATH)
    connection.send_and_get_reply(message_bus.AddMatch(rule), timeout=5)
    return connection


def test_emit_signal_reaches_another_connection(bus: SessionBusService) -> None:
    other = listener()

    bus.emit_signal(BusSignal(OBJECT_PATH, INTERFACE, "Changed", "s", ("now",)))

    message: Message = other.receive(timeout=5)
    other.close()
    assert (message.header.fields[3], message.body) == ("Changed", ("now",))


def test_emit_signal_does_nothing_when_stopped(qapp: object) -> None:
    SessionBusService(handler).emit_signal(
        BusSignal(OBJECT_PATH, INTERFACE, "Changed", "s", ("now",))
    )


def test_is_running_follows_start_and_stop(qapp: object) -> None:
    service = SessionBusService(handler)
    assert not service.is_running
    assert service.start(SERVICE_NAME)
    assert service.is_running
    service.stop()
    assert not service.is_running and service.unique_name == ""
