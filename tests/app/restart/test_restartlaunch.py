import pytest
from PySide6.QtCore import QProcess

from kondor.app.restart import launchenvironment, restartlaunch


def test_restart_words_end_with_restore_session_flag(monkeypatch):
    monkeypatch.setattr(restartlaunch.mcpcommand, "launch_words", lambda env: ["kondor"])
    assert restartlaunch.restart_words({}) == ["kondor", "--restore-session"]


def test_start_again_reports_failure(monkeypatch):
    monkeypatch.setattr(restartlaunch, "start_detached", lambda words, env: False)
    monkeypatch.setattr(restartlaunch, "restart_words", lambda env: ["kondor"])
    assert restartlaunch.start_again() is False


@pytest.fixture
def clean_launch_environment(monkeypatch):
    monkeypatch.setattr(launchenvironment, "_launch_environment", {})


def test_restart_environment_has_no_remote_debugging_set_after_launch(
    monkeypatch, clean_launch_environment
):
    monkeypatch.delenv("QTWEBENGINE_REMOTE_DEBUGGING", raising=False)
    launchenvironment.remember_launch_environment()
    monkeypatch.setenv("QTWEBENGINE_REMOTE_DEBUGGING", "127.0.0.1:9333")
    environment = launchenvironment.launch_environment()
    assert "QTWEBENGINE_REMOTE_DEBUGGING" not in environment


def test_process_environment_keeps_every_variable():
    result = restartlaunch.process_environment({"A": "1", "B": "2"})
    assert result.value("A") == "1" and result.value("B") == "2"


class FakeProcess:
    instances = []

    def __init__(self):
        self.flags = None
        FakeProcess.instances.append(self)

    def setProgram(self, program):
        pass

    def setArguments(self, arguments):
        pass

    def setProcessEnvironment(self, environment):
        pass

    def setUnixProcessParameters(self, flags):
        self.flags = flags

    def startDetached(self):
        return True


def test_start_detached_closes_inherited_file_descriptors(monkeypatch):
    monkeypatch.setattr(restartlaunch, "QProcess", FakeProcess)
    monkeypatch.setattr(FakeProcess, "UnixProcessFlag", QProcess.UnixProcessFlag, raising=False)
    restartlaunch.start_detached(["kondor"], {})
    assert FakeProcess.instances[-1].flags == QProcess.UnixProcessFlag.CloseFileDescriptors
