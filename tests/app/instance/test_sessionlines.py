import os

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QLocalSocket
from pytestqt.qtbot import QtBot

from kondor.app.instance import sessionprotocol
from kondor.app.instance.sessionprotocol import ClientIdentity, RemoteControlState
from kondor.app.instance.singleinstance import SingleInstance
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage

pytestmark = pytest.mark.usefixtures("qapp")
WAIT_MILLISECONDS = 2000
PORT = 9222


def test_routes_session_lines_apart_from_window_messages(qtbot: QtBot) -> None:
    name = f"kondor-test-session-{os.getpid()}"
    instance = SingleInstance(name)
    instance.start(SingleInstanceMessage())
    windows: list[object] = []
    sessions: list[object] = []
    instance.messageReceived.connect(windows.append)
    instance.sessionLineReceived.connect(lambda socket, parsed: sessions.append(parsed))
    client = QLocalSocket()
    client.connectToServer(name)
    assert client.waitForConnected(WAIT_MILLISECONDS)

    client.write(QByteArray(sessionprotocol.hello_line(ClientIdentity("Claude Code", "1"))))

    qtbot.waitUntil(lambda: len(sessions) == 1, timeout=WAIT_MILLISECONDS)
    assert windows == []
    assert sessionprotocol.parse_client(sessions[0]) == ClientIdentity("Claude Code", "1")
    client.disconnectFromServer()


def test_parses_the_reply_of_the_browser() -> None:
    line = sessionprotocol.reply_line(RemoteControlState(True, PORT))

    assert sessionprotocol.parse_reply(line) == RemoteControlState(True, PORT)


def test_ignores_a_reply_without_the_state() -> None:
    assert sessionprotocol.parse_reply(b"{}") is None
    assert sessionprotocol.parse_reply(b"nonsense") is None


def test_recognizes_only_session_lines() -> None:
    assert sessionprotocol.is_session_line(sessionprotocol.ports_line([1]))
    assert not sessionprotocol.is_session_line(b'{"urls":[]}')
