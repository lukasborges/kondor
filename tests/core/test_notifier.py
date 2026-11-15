import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication

from kondor.core import notifier
from kondor.core.notifier import Notifier, application_icon

FAKE_SERVER = Path(__file__).with_name("fakenotifications.py")
READY = "READY"
FLATPAK_ID = "io.github.lukasborges.Kondor"
SIGNATURE = "susssasa{sv}i"


def start_fake_server() -> subprocess.Popen[str]:
    command = [sys.executable, "-I", str(FAKE_SERVER)]
    return subprocess.Popen(command, stdout=subprocess.PIPE, text=True)


@pytest.fixture
def fake_server(qapp: object) -> Iterator[subprocess.Popen[str]]:
    server = start_fake_server()
    assert server.stdout is not None
    is_ready = server.stdout.readline().strip() == READY
    if not is_ready:
        server.wait()
        pytest.skip("org.freedesktop.Notifications is taken by another notification server")
    yield server
    server.kill()
    server.wait()


def test_notify_sends_the_freedesktop_signature(
    fake_server: subprocess.Popen[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    Notifier.instance().notify("Title", "Body", "")
    output, _ = fake_server.communicate(timeout=10)
    message = json.loads(output)
    name = QGuiApplication.applicationDisplayName()
    assert message["signature"] == SIGNATURE
    assert message["arguments"] == [name, 0, "kondor", "Title", "Body", [], {}, 5000]


def test_icon_name_kondor_uses_flatpak_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLATPAK_ID", FLATPAK_ID)
    assert application_icon("kondor") == FLATPAK_ID
    assert application_icon("dialog-information") == "dialog-information"


def test_notify_returns_without_waiting_for_the_bus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, qapp: object
) -> None:
    finished = tmp_path / "finished"
    slow = tmp_path / "slow-gdbus"
    slow.write_text(f"#!/bin/sh\nsleep 2\ntouch {finished}\n")
    slow.chmod(0o755)
    monkeypatch.setattr(notifier, "GDBUS_PROGRAM", str(slow))
    Notifier.instance().notify("Title", "Body", "")
    assert not finished.exists()
