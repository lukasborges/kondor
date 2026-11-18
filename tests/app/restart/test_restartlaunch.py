from kondor.app.restart import restartlaunch


def test_restart_words_end_with_restore_session_flag(monkeypatch):
    monkeypatch.setattr(restartlaunch.mcpcommand, "launch_words", lambda env: ["kondor"])
    assert restartlaunch.restart_words({}) == ["kondor", "--restore-session"]


def test_start_again_reports_failure(monkeypatch):
    monkeypatch.setattr(restartlaunch, "start_detached", lambda words: False)
    monkeypatch.setattr(restartlaunch, "restart_words", lambda env: ["kondor"])
    assert restartlaunch.start_again() is False
