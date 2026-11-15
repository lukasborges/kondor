import os

import pytest

from kondor.app.remotecontrol import remotecontrolenvironment as environment

DEBUGGING = environment.DEBUGGING_VARIABLE
FLAGS = environment.FLAGS_VARIABLE


def test_enabling_binds_the_local_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DEBUGGING, raising=False)
    monkeypatch.delenv(FLAGS, raising=False)

    environment.enable_debugging(9333)

    assert os.environ[DEBUGGING] == "127.0.0.1:9333"


def test_enabling_allows_only_the_local_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(FLAGS, raising=False)

    environment.enable_debugging(9333)

    assert os.environ[FLAGS] == "--remote-allow-origins=http://127.0.0.1:9333"


def test_enabling_keeps_the_existing_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAGS, "--no-sandbox")

    environment.enable_debugging(9333)

    assert os.environ[FLAGS] == "--no-sandbox --remote-allow-origins=http://127.0.0.1:9333"


def test_disabling_removes_a_variable_left_in_the_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DEBUGGING, "9222")

    environment.disable_debugging()

    assert DEBUGGING not in os.environ
