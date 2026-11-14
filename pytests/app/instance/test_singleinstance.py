import os
from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray, QUrl
from PySide6.QtNetwork import QLocalSocket
from pytestqt.qtbot import QtBot

from kondor.app.instance.singleinstance import MAX_MESSAGE_SIZE, SingleInstance, StartResult
from kondor.app.instance.singleinstancemessage import (
    SingleInstanceMessage,
    from_json_line,
    to_json_line,
)
from pytests.qmlsupport import captured_messages

pytestmark = pytest.mark.usefixtures("qapp")
WAIT_MILLISECONDS = 2000
TWO_MESSAGES = 2


def unique_name(label: str) -> str:
    return f"kondor-test-{label}-{os.getpid()}"


def private_url_message() -> SingleInstanceMessage:
    return SingleInstanceMessage([QUrl("https://kde.org")], True, False, b"token")


def test_socket_name_depends_on_profile_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "first"))
    first = SingleInstance.server_name()
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "second"))
    second = SingleInstance.server_name()

    assert first.endswith(".socket")
    assert "/kondor-" in first
    assert first != second


def test_encodes_and_decodes_message() -> None:
    message = SingleInstanceMessage(
        [QUrl("https://kde.org"), QUrl.fromLocalFile("/tmp/a page.html")],
        True,
        True,
        b"activation-token",
    )

    encoded = to_json_line(message)

    assert encoded.endswith(b"\n")
    assert encoded.count(b"\n") == 1
    assert from_json_line(encoded) == message


def test_rejects_invalid_data() -> None:
    assert from_json_line(b"not json") == SingleInstanceMessage()


def test_message_bytes_match_the_cpp_format() -> None:
    message = private_url_message()
    message.activation_token = b"t"

    assert to_json_line(message) == (
        b'{"activationToken":"t","newWindow":false,"private":true,"urls":["https://kde.org"]}\n'
    )


def test_forwards_message_to_running_instance(qtbot: QtBot) -> None:
    name = unique_name("forward")
    server = SingleInstance(name)
    assert server.start(SingleInstanceMessage()) is StartResult.LISTENING

    with qtbot.waitSignal(server.messageReceived, timeout=WAIT_MILLISECONDS) as received:
        assert SingleInstance(name).send_message(private_url_message())

    assert received.args == [private_url_message()]


def test_forwards_when_another_instance_started_first(qtbot: QtBot) -> None:
    name = unique_name("race")
    running = SingleInstance(name)
    assert running.start(SingleInstanceMessage()) is StartResult.LISTENING

    with qtbot.waitSignal(running.messageReceived, timeout=WAIT_MILLISECONDS):
        later = SingleInstance(name)
        assert later.start(SingleInstanceMessage()) is StartResult.FORWARDED


def write_raw(name: str, data: bytes) -> QLocalSocket:
    socket = QLocalSocket()
    socket.connectToServer(name)
    assert socket.waitForConnected(WAIT_MILLISECONDS)
    socket.write(QByteArray(data))
    socket.flush()
    return socket


def test_two_messages_in_one_write_give_two_signals(qtbot: QtBot) -> None:
    name = unique_name("twice")
    server = SingleInstance(name)
    server.start(SingleInstanceMessage())
    received: list[object] = []
    server.messageReceived.connect(received.append)
    first = to_json_line(SingleInstanceMessage([QUrl("https://a.example")]))
    second = to_json_line(SingleInstanceMessage([QUrl("https://b.example")]))

    socket = write_raw(name, first + second)

    qtbot.waitUntil(lambda: len(received) == TWO_MESSAGES, timeout=WAIT_MILLISECONDS)
    socket.disconnectFromServer()


def test_oversized_message_is_ignored(qtbot: QtBot) -> None:
    name = unique_name("big")
    server = SingleInstance(name)
    server.start(SingleInstanceMessage())
    received: list[object] = []
    server.messageReceived.connect(received.append)

    with captured_messages() as messages:
        socket = write_raw(name, b"x" * (MAX_MESSAGE_SIZE + 1))
        qtbot.waitUntil(lambda: bool(messages), timeout=WAIT_MILLISECONDS)

    assert "single-instance message too large, ignored" in messages[0]
    assert received == []
    socket.disconnectFromServer()
