from kondor.app.restart import launchenvironment, restartlaunch


def test_restart_words_end_with_restore_session_flag(monkeypatch):
    monkeypatch.setattr(restartlaunch.mcpcommand, "launch_words", lambda env: ["kondor"])
    assert restartlaunch.restart_words({}) == ["kondor", "--restore-session"]


def test_start_again_reports_failure(monkeypatch):
    monkeypatch.setattr(restartlaunch, "start_detached", lambda words, env: False)
    monkeypatch.setattr(restartlaunch, "restart_words", lambda env: ["kondor"])
    assert restartlaunch.start_again() is False


def test_restart_environment_has_no_remote_debugging_set_after_launch(monkeypatch):
    monkeypatch.delenv("QTWEBENGINE_REMOTE_DEBUGGING", raising=False)
    launchenvironment.remember_launch_environment()
    monkeypatch.setenv("QTWEBENGINE_REMOTE_DEBUGGING", "127.0.0.1:9333")
    environment = launchenvironment.launch_environment()
    assert "QTWEBENGINE_REMOTE_DEBUGGING" not in environment


def test_process_environment_keeps_every_variable():
    result = restartlaunch.process_environment({"A": "1", "B": "2"})
    assert result.value("A") == "1" and result.value("B") == "2"
