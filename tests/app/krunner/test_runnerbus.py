from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import QProcess
from pytestqt.qtbot import QtBot

from kondor.app.krunner.runnerbus import OBJECT_PATH, SERVICE_NAME, Reply, RunnerBus


def handler(member: str, body: tuple[Any, ...]) -> Reply | None:
    return ("s", (f"{member}:{body[0]}",)) if member == "Match" else None


@pytest.fixture
def bus(qapp: object) -> Iterator[RunnerBus]:
    runner = RunnerBus(handler)
    assert runner.start()
    yield runner
    runner.stop()


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
        qtbot, "--dest", SERVICE_NAME, "--object-path", OBJECT_PATH, "--method", method, "kon"
    )


def test_start_owns_the_service_name(bus: RunnerBus, qtbot: QtBot) -> None:
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


def test_second_bus_does_not_start(bus: RunnerBus) -> None:
    second = RunnerBus(handler)

    assert second.start() is False


def test_match_call_gets_the_handler_reply(bus: RunnerBus, qtbot: QtBot) -> None:
    code, output = call(qtbot, "org.kde.krunner1.Match")

    assert "Match:kon" in output, (code, output)


def test_unknown_method_gets_an_error(bus: RunnerBus, qtbot: QtBot) -> None:
    code, output = call(qtbot, "org.kde.krunner1.Nothing")

    assert "UnknownMethod" in output, (code, output)


def test_stop_releases_the_name(qapp: object, qtbot: QtBot) -> None:
    first = RunnerBus(handler)
    assert first.start()
    first.stop()
    second = RunnerBus(handler)

    assert second.start()
    second.stop()
